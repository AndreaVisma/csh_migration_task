from urllib.request import urlretrieve
import zipfile
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import contextily as cx

msa = gpd.read_file('data/tl_2019_us_cbsa/tl_2019_us_cbsa.shp')
msa = msa[['CBSAFP', 'geometry']].rename(columns = {'CBSAFP' : 'msa_cd1'})
msa.msa_cd1 = msa.msa_cd1.astype('int64')

#load movements file previously produced
move = pd.read_excel('data/movement_pairs.xlsx')

#produce network for movers to and from the US
move.loc[move.curr_res.str.contains('Outside'), 'curr_res'] = 'US or PR non MA'
move.loc[move.curr_res.str.len() > 18, 'curr_res'] = 'US MA'

move.loc[move.res_1y_ago.str.contains('Outside'), 'res_1y_ago'] = 'US or PR non MA'
move.loc[move.res_1y_ago.str.len() > 18, 'res_1y_ago'] = 'US MA'

#plot chord diagram
from d3blocks import D3Blocks

d3 = D3Blocks()
move.rename(columns={'curr_res':'target', 'res_1y_ago':'source',
                     'flow_est' : 'weight'}, inplace = True)
move_no_ma_to_ma = move[move.source != move.target]

d3.chord(move, filepath='plots/migration_chord.html')
d3.chord(move_no_ma_to_ma, filepath='plots/migration_chord_without_MtM.html')