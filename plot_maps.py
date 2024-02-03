from urllib.request import urlretrieve
import zipfile
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import contextily as cx

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
fig.savefig('plots/dist_inflows.png', bbox_inches = 'tight')

#plot map for total estimated inflows
fig, ax = plt.subplots(figsize=(15, 10))
tot_inflow.plot(column = 'flow_est',
                legend=True,
                scheme="prettybreaks",
                cmap = 'viridis',
                ax = ax
                )
cx.add_basemap(ax, crs=tot_inflow.crs.to_string(),
               source = cx.providers.CartoDB.VoyagerNoLabels)
ax.set_xlim(-130, -65)
ax.set_ylim(23, 55)

#annotate the MSAs with large inflows
large_inflow = tot_inflow[tot_inflow.flow_est > 300_000].merge(
    move[['curr_res', 'curr_res_cd1']], left_on='msa_cd1', right_on='curr_res_cd1',
    how = 'left'
)
for x, y, label in zip(large_inflow.geometry.centroid.x,
                       large_inflow.geometry.centroid.y,
                       large_inflow.curr_res):
    ax.annotate(label.split('-')[0], xy=(x, y), xytext=(3, 3),
                textcoords="offset points", color = 'red')

fig.savefig('plots/map_inflows.png', bbox_inches = 'tight')


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

#plot map for total estimated outflows
fig, ax = plt.subplots(figsize=(15, 10))
tot_outflow.plot(column = 'flow_est',
                legend=True,
                scheme="prettybreaks",
                cmap = 'viridis',
                ax = ax)
cx.add_basemap(ax, crs=tot_outflow.crs.to_string(),
               source = cx.providers.CartoDB.VoyagerNoLabels)
ax.set_xlim(-130, -65)
ax.set_ylim(23, 55)

large_outflow = tot_outflow[tot_inflow.flow_est > 300_000].merge(
    move[['curr_res', 'curr_res_cd1']], left_on='msa_cd1', right_on='curr_res_cd1',
    how = 'left'
)
for x, y, label in zip(large_outflow.geometry.centroid.x,
                       large_outflow.geometry.centroid.y,
                       large_outflow.curr_res):
    ax.annotate(label.split('-')[0], xy=(x, y), xytext=(3, 3),
                textcoords="offset points", color = 'red')

ax.figure.savefig('plots/map_outflows.png')

