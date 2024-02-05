import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import geopandas as gpd
from shapely import wkt
import numpy as np
from d3blocks import D3Blocks
import matplotlib.pyplot as plt

msa = gpd.read_file('data/tl_2019_us_cbsa/tl_2019_us_cbsa.shp')
msa = msa[['CBSAFP', 'geometry']].rename(columns = {'CBSAFP' : 'msa_cd1'})
msa.msa_cd1 = msa.msa_cd1.astype('int64')

#load movements file previously produced
move = pd.read_excel('data/movement_pairs.xlsx')

#print some descriptive info
print(f"""Total relocations: {move['flow_est'].sum()}
- - - - - - - - - 
lower bound 90% confidence interval: {move['min_flow'].sum()}
upper bound 90% confidence interval: {move['max_flow'].sum()}
- - - - - - - - - """)

#produce network for movers to and from the US
move.loc[move.curr_res.str.contains('Outside'), 'curr_res'] = 'US or PR non MSA'
move.loc[move.curr_res.str.len() > 18, 'curr_res'] = 'US MSA'

move.loc[move.res_1y_ago.str.contains('Outside'), 'res_1y_ago'] = 'US or PR non MSA'
move.loc[move.res_1y_ago.str.len() > 18, 'res_1y_ago'] = 'US MSA'

#calculate percentages
totals = (move[['curr_res', 'res_1y_ago', 'flow_est']]
    .groupby(['curr_res', 'res_1y_ago']).sum()).reset_index()
totals.loc[totals.res_1y_ago.str.contains('U.S.'), 'res_1y_ago'] = 'US Islands'
tot_flow = totals.flow_est.sum()
totals['pct_total'] = 100 * totals.flow_est/tot_flow

#save as it might be useful
totals.to_excel('data/macro_areas_flows.xlsx', index = False)
immigration = (totals[~totals.res_1y_ago.str.contains('US')].
               groupby('res_1y_ago').sum().sort_values('flow_est', ascending = False).
               reset_index())

print(f"""Intra-US migration: {round(totals[totals.res_1y_ago.str.contains('US')]['pct_total'].sum(), 2)} of total
- - - - - - - - - -
Migration between MSAs: {round(totals[(totals.res_1y_ago == 'US MSA') & (totals.curr_res == 'US MSA')]['pct_total'].sum(), 2)} of total
- - - - - - - - - -
Migration from abroad: {round(totals[~totals.res_1y_ago.str.contains('US')]['pct_total'].sum(), 2)} of total
-> makes sense, as it sums to 100%
- - - - - - - - - - -
Top 3 areas of immigration:
{immigration.res_1y_ago[0]} : {round(immigration.pct_total[0], 2)}%
{immigration.res_1y_ago[1]} : {round(immigration.pct_total[1], 2)}%
{immigration.res_1y_ago[2]} : {round(immigration.pct_total[2], 2)}%
""")

#plot chord diagram
d3 = D3Blocks()
move.rename(columns={'curr_res':'target', 'res_1y_ago':'source',
                     'flow_est' : 'weight'}, inplace = True)
move_no_ma_to_ma = move[move.source != move.target]

d3.chord(move, filepath='plots/migration_chord.html')
d3.chord(move_no_ma_to_ma, filepath='plots/migration_chord_without_MtM.html')

# calculate distance of migration for each origin-destination pair
dict_msa_geo = pd.Series(msa.geometry.values,index=msa.msa_cd1).to_dict()

move['geometry_dest'] = move['curr_res_cd1'].map(dict_msa_geo)
move = move[move.res_1y_ago_cd1.str.isnumeric()] #remove people that came from abroad
move.res_1y_ago_cd1 = move.res_1y_ago_cd1.astype('int64')
move['geometry_origin'] = move['res_1y_ago_cd1'].map(dict_msa_geo)

#keep M to M movement
move = move.dropna()
#convert into equal-area projection
print("Calculating the distance between MSAs. This is gonna take a little ...")
move['distance'] = (gpd.GeoSeries(move['geometry_dest'], crs = 'EPSG:4269').to_crs('EPSG:9822').centroid.
                    distance(
    gpd.GeoSeries(move['geometry_origin'], crs = 'EPSG:4269').to_crs('EPSG:9822').centroid))
print("Done with calculating distance!")
move['distance'] = move['distance'].astype('int') / 1_000 #convert to km

#plot relationship between flow and distance
fig, ax = plt.subplots()
ax.scatter(move['distance'], move['weight'], alpha=0.8)
plt.show()

high_move = move[move.weight > 5_000]
fig, ax = plt.subplots()
ax.scatter(high_move['distance'], high_move['weight'], alpha=0.8)
plt.show()

weight = high_move.copy()
weight['weight'] /= 2_000
weight['weight'] = weight['weight'].astype('int')
weight = weight.reindex(weight.index.repeat(weight['weight']))

fig, ax = plt.subplots(figsize =(4,6))
bp_dict = weight.boxplot(column='distance',
                           ax=ax, return_type='dict')
def add_values(bp, ax):
    """ This actually adds the numbers to the various points of the boxplots"""
    for element in ['whiskers', 'medians', 'caps']:
        for line in bp[element]:
            # Get the position of the element. y is the label you want
            (x_l, y),(x_r, _) = line.get_xydata()
            # Make sure datapoints exist
            # (I've been working with intervals, should not be problem for this case)
            if not np.isnan(y):
                x_line_center = x_l + (x_r - x_l)/2
                y_line_center = y  # Since it's a line and it's horisontal
                # overlay the value:  on the line, from center to right
                ax.text(x_line_center + 0.2, y_line_center, # Position
                        '%.3f' % y, # Value (3f = 3 decimal float)
                        verticalalignment='center', # Centered vertically with line
                        fontsize=6, backgroundcolor="white")
add_values(bp_dict, ax)
ax.boxplot(weight['distance'])
plt.ylabel('Migration distance in km, weighted by flow')
plt.tick_params(axis='x', bottom = False, labelbottom = False)
fig.savefig('plots/distance_boxplot.svg', bbox_inches = 'tight')
plt.show()
