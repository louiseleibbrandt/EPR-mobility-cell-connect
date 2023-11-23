import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import re
import numpy as np

# Start and End date for trajectory analysis
start_date = '2023-07-01'
end_date = '2023-07-31'

df_cell = pd.read_csv('./outputs/trajectories/Final_Eval/Returner/output_cell200.csv')


mask = (df_cell['timestamp'] >= start_date) & (df_cell['timestamp'] <= end_date)
df_cell = df_cell.loc[mask]




agents = sorted(pd.unique(df_cell['owner']))
overlap = np.diag(np.zeros(len(agents)))
for i in range(len(agents)):
    for j in range(i+1,len(agents)):
        agents_cell1 = df_cell[df_cell['owner'].isin([agents[i]])] 
        agents_cell2 = df_cell[df_cell['owner'].isin([agents[j]])] 
        phone1_df = agents_cell1[agents_cell1['device'].isin([re.sub("[^0-9]", "", agents[i])+"_1"])] 
        phone2_df = agents_cell2[agents_cell2['device'].isin([re.sub("[^0-9]", "", agents[j])+"_1"])] 
        df1 = (pd.DataFrame({'lon': phone1_df['cellinfo.wgs84.lon'], 'lat': phone1_df['cellinfo.wgs84.lat']})).drop_duplicates()
        df2 = (pd.DataFrame({'lon': phone2_df['cellinfo.wgs84.lon'], 'lat': phone2_df['cellinfo.wgs84.lat']})).drop_duplicates()
        concat = (pd.concat([df1, df2])).drop_duplicates()
        # print("new line")
        # print(df1)
        # print(df2)
        # print(concat)

        overlap[i][j] = 1- len(concat)/(len(df1)+len(df2))
        overlap[j][i] = 1- len(concat)/(len(df1)+len(df2))

least_overlapping = []
print(overlap)
mat=np.matrix(overlap)
with open('./outputs/trajectories/Final_Eval/Returner/outfile200.txt','wb') as f:
    for line in mat:
        np.savetxt(f, line, fmt='%.2f')


