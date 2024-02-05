from urllib.request import urlretrieve
import zipfile
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import contextily as cx
import os

#create a folder to save the plots, if missing
#make the directory to save the data
try:
    os.mkdir('plots')
except:
    print("The folder 'plots' already exists")

#download MSA shapefiles
url = ('https://www2.census.gov/geo/tiger/TIGER2019/CBSA/tl_2019_us_cbsa.zip')
filename = "data/tl_2019_us_cbsa.zip"
urlretrieve(url, filename)

#unzip it so we can load it with geopandas
with zipfile.ZipFile(filename, 'r') as zip_ref:
    zip_ref.extractall('data/tl_2019_us_cbsa')

msa = gpd.read_file('data/tl_2019_us_cbsa/tl_2019_us_cbsa.shp')
msa = msa[['CBSAFP', 'geometry']].rename(columns = {'CBSAFP' : 'msa_cd1'})
msa.msa_cd1 = msa.msa_cd1.astype('int64')

#load movements file previously produced
move = pd.read_excel('data/movement_pairs.xlsx')

#calculate total inflow per MSA and merge with geography
tot_inflow = (move[['curr_res_cd1', 'flow_est', 'min_flow', 'max_flow']].
              groupby('curr_res_cd1').sum())
tot_inflow = (msa.merge(tot_inflow, right_on = 'curr_res_cd1', #merge this way to maintain Geopandas geometry
                        left_on = 'msa_cd1' ,how = 'right')
              .sort_values('flow_est', ascending = False))
tot_inflow = tot_inflow[~tot_inflow.msa_cd1.isna()] #remove people that moved abroad, or to a non MSA area

#plot distribution for total estimated inflows
fig, ax = plt.subplots()
tot_inflow["flow_est"].hist(bins=50, ax = ax)
plt.xlabel("Inflows\nEstimated arrivals in the past year")
plt.ylabel("Number of Metropolitan Statistical Areas")
plt.title("Distribution of MSAs by number of new settlements, US")
fig.savefig('plots/distr_inflows.svg', bbox_inches = 'tight')
plt.show()

#print some info
print(f"""
mean inflow: {tot_inflow.flow_est.mean()},
percentage MSAs with inflows < 100_000 : {100 * len(tot_inflow[tot_inflow.flow_est < 100_000])/len(tot_inflow)}""")

#plot map for total estimated inflows
fig, ax = plt.subplots(figsize=(7, 5))
tot_inflow.plot(column = 'flow_est',
                legend=True,
                legend_kwds={'fontsize': 'small'},
                scheme="prettybreaks",
                cmap = 'viridis',
                ax = ax
                )
cx.add_basemap(ax, crs=tot_inflow.crs.to_string(),
               source = cx.providers.CartoDB.VoyagerNoLabels)
ax.set_xlim(-125, -60)
ax.set_ylim(23, 57)
plt.axis('off')

#annotate the MSAs with names of largest inflows' MSAs
large_inflow = tot_inflow[tot_inflow.flow_est > 300_000].merge(
    move[['curr_res', 'curr_res_cd1']], left_on='msa_cd1', right_on='curr_res_cd1',
    how = 'left'
)
for x, y, label in zip(large_inflow.geometry.centroid.x,
                       large_inflow.geometry.centroid.y,
                       large_inflow.curr_res):
    ax.annotate(label.split('-')[0], xy=(x, y), xytext=(3, 3),
                textcoords="offset points", color = 'red')

fig.savefig('plots/map_inflows.svg', bbox_inches = 'tight')
plt.show()

##now the same with outflows
#calculate total outflow per MSA and merge with geography
tot_outflow = (move[['res_1y_ago_cd1', 'flow_est', 'min_flow', 'max_flow']].
              groupby('res_1y_ago_cd1').sum()).reset_index()
tot_outflow = tot_outflow[tot_outflow.res_1y_ago_cd1.str.isnumeric()] #remove people that came from abroad
tot_outflow.res_1y_ago_cd1 = tot_outflow.res_1y_ago_cd1.astype('int64')
tot_outflow = tot_outflow[tot_outflow.res_1y_ago_cd1 != 99999]
tot_outflow = (msa.merge(tot_outflow, left_on = 'msa_cd1',
                         right_on = 'res_1y_ago_cd1', how = 'right')
              .sort_values('flow_est', ascending = False))

#plot distribution for total estimated outflows
fig, ax = plt.subplots()
tot_outflow["flow_est"].hist(bins=50)
plt.xlabel("outflows\nEstimated arrivals in the past year")
plt.ylabel("Number of Metropolitan Statistical Areas")
plt.title("Distribution of MSAs by number of new settlements, US")
fig.savefig('plots/dist_outflows.png', bbox_inches = 'tight')
plt.show()

#plot map for total estimated outflows
fig, ax = plt.subplots(figsize=(7, 5))
tot_outflow.plot(column = 'flow_est',
                legend=True,
                legend_kwds = {'fontsize': 'small'},
                scheme="prettybreaks",
                cmap = 'viridis',
                ax = ax)
cx.add_basemap(ax, crs=tot_outflow.crs.to_string(),
               source = cx.providers.CartoDB.VoyagerNoLabels)
ax.set_xlim(-125, -60)
ax.set_ylim(23, 57)
plt.axis('off')

large_outflow = tot_outflow[tot_inflow.flow_est > 300_000].merge(
    move[['curr_res', 'curr_res_cd1']], left_on='msa_cd1', right_on='curr_res_cd1',
    how = 'left'
)
for x, y, label in zip(large_outflow.geometry.centroid.x,
                       large_outflow.geometry.centroid.y,
                       large_outflow.curr_res):
    ax.annotate(label.split('-')[0], xy=(x, y), xytext=(3, 3),
                textcoords="offset points", color = 'red')

fig.savefig('plots/map_outflows.svg', bbox_inches = 'tight')
plt.show()

# difference between inflows and outflows
diff_flows = (tot_inflow[['msa_cd1', 'flow_est']].rename(columns = {'flow_est' : 'inflow'}).
              merge(tot_outflow[['msa_cd1', 'flow_est']].
                    rename(columns = {'flow_est' : 'outflow'}), on = 'msa_cd1'))

diff_flows['flow_diff'] = diff_flows['inflow'] - diff_flows['outflow']
#re-merge into geodataframe to plot
diff_flows = (msa.merge(diff_flows, on = 'msa_cd1', how = 'right'))

fig, ax = plt.subplots(figsize=(7.5, 5))
diff_flows.plot(column = 'flow_diff',
                legend=True,
                legend_kwds={'fontsize': 'small'},
                scheme="prettybreaks",
                cmap = 'coolwarm_r',
                ax = ax)
cx.add_basemap(ax, crs=tot_outflow.crs.to_string(),
               source = cx.providers.CartoDB.VoyagerNoLabels)
ax.set_xlim(-125, -60)
ax.set_ylim(23, 57)
plt.axis('off')
fig.savefig('plots/difference_migration_flows_map.svg', bbox_inches = 'tight')
plt.show()

## size of MSA population vs inflow
curr_msa_info = pd.read_excel('data/curr_msa_info.xlsx')
flow_size = (tot_inflow[['msa_cd1', 'flow_est']].
             merge(curr_msa_info, left_on='msa_cd1',
                   right_on = 'curr_res_cd1', how='inner'))

assert not flow_size.curr_res_cd1.duplicated().any() #make sure no duplicates are there for some reason

#check if there are differences in the estimates
flow_size['inmovers'] = (flow_size['curr_res_movers_diff_metro_est']+
                         flow_size['curr_res_movers_from_else_US_PR_est'] +
                         flow_size['curr_res_movers_abroad_est'])
flow_size['diff_estimates'] = flow_size['flow_est'] - flow_size['inmovers']
flow_size['diff_estimates'].plot()
plt.show()
# perfectly equal, nice sign of data cleanliness, I guess :)

#check relationship between inflow and MSA fixed pop size
flow_size['permanent_pop'] = flow_size['curr_res_pop_over_1y_est'] + flow_size['curr_res_Nonmovers_est']

fig, ax = plt.subplots(figsize=(6,4))
sns.regplot(data=flow_size, x="permanent_pop", y="flow_est",
            ci = 90, order=2, line_kws=dict(color="r"), ax = ax)
plt.xlabel('Estimated permanent population in each MSA')
plt.ylabel('Estimated migration inflow in each MSA')
fig.savefig('plots/permanent_vs_inflow.svg', bbox_inches = 'tight')
plt.show()

large_msa = flow_size[flow_size.permanent_pop > 1.5e7]








