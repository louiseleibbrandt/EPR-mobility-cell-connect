import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np

import csv
from pyproj import Transformer
from scipy.stats import poisson
from datetime import datetime, timedelta

import random
from math import atan2,degrees

# Setup output file
output_file = open('./outputs/trajectories/output_cell.csv', 'w')
output_writer = csv.writer(output_file)
output_writer.writerow(['id','owner','device','timestamp','cellinfo.wgs84.lon','cellinfo.wgs84.lat','cellinfo.azimuth_degrees','cell'])    

bounding_box = (4.2009,51.8561,4.5978,52.1149)

# Start and End date for trajectory analysis
start_date = '2023-05-01'
end_date = '2023-05-05'

# Read in cell and trajectory data
df_cell = pd.read_csv('./data/20191202131001.csv')
df_trajectory = pd.read_csv('./outputs/trajectories/output_trajectory.csv')

# extra refinements trajectory
mask = (df_trajectory['timestamp'] >= start_date) & (df_trajectory['timestamp'] <= end_date)
df_trajectory = df_trajectory.loc[mask]
start = datetime.strptime(start_date,"%Y-%m-%d")
df_trajectory['seconds'] = [(datetime.strptime(x,"%Y-%m-%d %H:%M:%S") - start).total_seconds() for x in df_trajectory['timestamp']]

# extra refinements cell
df_cell['lon'],df_cell['lat'] =  Transformer.from_crs("EPSG:28992","EPSG:4979").transform(df_cell['X'],df_cell['Y'])
df_cell = df_cell.loc[(df_cell['lat'] >= bounding_box[0]) & (df_cell['lat'] <= bounding_box[2]) & (df_cell['lon'] >= bounding_box[1]) & (df_cell['lon'] <= bounding_box[3])]
df_cell['Hoofdstraalrichting'] = df_cell['Hoofdstraalrichting'].str.replace('\D', '')
df_cell['Hoofdstraalrichting'] = df_cell['Hoofdstraalrichting'].str.replace(' ', '')



agents = sorted(pd.unique(df_trajectory['owner']))

all_cells = np.array(list(zip(df_cell['lat'],df_cell['lon'])))
writing_id = 0

for i in range(len(agents)):
    agents_df = df_trajectory[df_trajectory['owner'].isin([agents[i]])] 
    max = agents_df['seconds'].iloc[-1]

    for phone in range(2):
        index = 0
        p_time = poisson.rvs(600)
        x_old, y_old = 0,0
        cellx, celly, degree = 0,0,0


        while(p_time <= max):
            while (agents_df['seconds'].iloc[index] <= p_time):
                index += 1
            print(index)
            x = agents_df['cellinfo.wgs84.lon'].iloc[index-1]
            y = agents_df['cellinfo.wgs84.lat'].iloc[index-1]

            if (x_old != x or y_old != y):
                position = np.array((x,y))
                distances = np.linalg.norm(all_cells-position, axis=1)
                found = False

                while (not found):
                    index_dis = np.argmin(distances)
                    degree_cell = df_cell['Hoofdstraalrichting'].iloc[index_dis]
                    degree_actual = (degrees(atan2(y-all_cells[index_dis][1], x-all_cells[index_dis][0]))+360)%360
                    if (degree_actual >= int(degree_cell) - 60 and degree_actual <= int(degree_cell) + 60):
                        found = True
                    else:
                        distances[index_dis] = float('inf')
                
                cellx = all_cells[index_dis][0]
                celly = all_cells[index_dis][1]
                degree = degree_cell
                x_old = x
                y_old = y

            output_writer.writerow([writing_id, f"Agent{i}", f"{i}_{phone+1}", 
                        start + timedelta(seconds = p_time), cellx, celly, degree,"0-0-0"])
            
            p_time += poisson.rvs(300)
            writing_id += 1


output_file.close()
