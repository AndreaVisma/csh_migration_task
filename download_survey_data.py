from urllib.request import urlretrieve
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import numpy as np

url = ("https://www2.census.gov/programs-surveys/demo/tables/geographic-mobility"
       "/2019/metro-to-metro-migration/metro-to-metro-2015-2019.xlsx")
filename = "data/metro-to-metro-2015-2019.xlsx"
urlretrieve(url, filename)

#import df noting that col headers are split over 3 rows
df = pd.read_excel(filename, header = [1,2,3])

#remove names empty rows, so we can merge the multilevel columns into 1 level
for i, columns_old in enumerate(df.columns.levels):
    columns_new = np.where(columns_old.str.contains('Unnamed'), '', columns_old)
    df.rename(columns=dict(zip(columns_old, columns_new)), level=i, inplace=True)

df.columns = df.columns.map(','.join).str.strip(',')
df.columns = df.columns.str.replace(',', '_')
df.columns = df.columns.str.replace('__', '_') #sometimes there were two commas in a row

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
                  'Movers in Metro-to-Metro Flow' : 'm_to_m_flow',
                  'Estimate' : 'est'}

for k, v in names_to_change.items():
    df.columns = df.columns.str.replace(k, v)

df.to_csv('data/m_to_m_clean_cols.csv')
