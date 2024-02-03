from urllib.request import urlretrieve
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import numpy as np
import os

#make the directory to save the data
try:
    os.mkdir('data')
except:
    print("The folder 'data' already exists ;)")

#download and save the survey data
url = ("https://www2.census.gov/programs-surveys/demo/tables/geographic-mobility"
       "/2019/metro-to-metro-migration/metro-to-metro-2015-2019.xlsx")
filename = "data/metro-to-metro-2015-2019.xlsx"
urlretrieve(url, filename)

#import df noting that col headers are split over 3 rows
df = pd.read_excel(filename, header = [1,2,3])

#remove names of the empty column rows
for i, columns_old in enumerate(df.columns.levels):
    columns_new = np.where(columns_old.str.contains('Unnamed'), '', columns_old)
    df.rename(columns=dict(zip(columns_old, columns_new)), level=i, inplace=True)
#merge the multilevel columns into 1 level
df.columns = df.columns.map(','.join).str.strip(',')

#change some names to make accessing columns easier
names_to_change ={'Current Residence Metro Code1' : 'curr_res_cd1',
                  'Residence 1 Year Ago Metro Code1' : 'res_1y_ago_cd1',
                  'Metropolitan Statistical Area of Current Residence' : 'curr_res',
                  'Metropolitan Statistical Area of Residence 1 Year Ago' : 'res_1y_ago',
                  'Population 1 Year and Over' : 'pop_over_1y',
                  'Movers within Same Metropolitan Statistical Area' : 'movers_same_metro',
                  'Movers from Different Metropolitan Statistical Area2' : 'movers_diff_metro',
                  'Movers from Elsewhere in the U.S. or Puerto Rico' : 'movers_from_else_US_PR',
                  'Movers to Elsewhere in the U.S. or Puerto Rico' : 'movers_to_else_US_PR',
                  'Movers from Abroad3' : ' movers_abroad',
                  'Movers in Metro-to-Metro Flow' : 'flow',
                  'Estimate' : 'est'}

for k, v in names_to_change.items():
    df.columns = df.columns.str.replace(k, v)

df.columns = df.columns.str.replace(',', '_')
df.columns = df.columns.str.replace(' ', '')
df.columns = df.columns.str.replace('__', '_') #sometimes there were two commas in a row

#save the cleaner data as csv, might be useful
df.to_csv('data/m_to_m_clean_cols.csv')

####
# construct some additional dataset
####

# current info for each individual MSA
indiv_msa_info_curr = df[[x for x in df.columns if 'curr' in x]].groupby('curr_res').agg('first').reset_index()
indiv_msa_info_curr.to_excel('data/current_msa_info.xlsx', index = False)

#movements for each MSA pair
movement_pairs = df[['curr_res', 'curr_res_cd1', 'res_1y_ago', 'res_1y_ago_cd1',
                     'flow_est', 'flow_MOE']].copy()
movement_pairs['min_flow'] = movement_pairs.flow_est - movement_pairs.flow_MOE
movement_pairs.loc[movement_pairs['min_flow'] < 0, 'min_flow'] = 0 #cap the minimum flow to be nonnegative
movement_pairs['max_flow'] = movement_pairs.flow_est + movement_pairs.flow_MOE

movement_pairs.sort_values('flow_est', ascending = False, inplace = True)

#check for NaNs and drop them
print(f""" number of missing values per column:
- - - - - - - - - - - - -
{movement_pairs.isna().sum()}""")
movement_pairs.dropna(inplace = True)

movement_pairs.to_excel('data/movement_pairs.xlsx', index = False)