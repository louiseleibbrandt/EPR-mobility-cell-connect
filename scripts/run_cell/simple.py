import pandas as pd
import numpy as np
import re
import csv

from pyproj import Transformer
from datetime import datetime, timedelta
from math import atan2,degrees
from config import BOUNDING_BOX, BOUNDING_INCREASE, START_DATE, END_DATE, OUTPUT_TRAJECTORY_FILE, OUTPUT_CELL_FILE, CELL_FILE

def main(model_params):
    # Retrieve start date
    start = datetime.strptime(model_params["start_date"],"%Y-%m-%d")

    # Expand bounding box size
    increase = BOUNDING_INCREASE

    # Setup output file
    output_file = open(model_params["output_file"], 'w')
    output_writer = csv.writer(output_file)
    output_writer.writerow(['id','owner','device','timestamp','cellinfo.wgs84.lon','cellinfo.wgs84.lat','cellinfo.azimuth_degrees','cell'])    

    # Read in cell towers, transform lon/lat, limit to bounding box, format the orientation data
    df_cell = pd.read_csv(model_params["cell_file"])
    df_cell['lon'],df_cell['lat'] =  Transformer.from_crs("EPSG:28992","EPSG:4979").transform(df_cell['X'],df_cell['Y'])
    df_cell = df_cell.loc[(df_cell['lat'] >= model_params["bounding_box"][0] - increase) & (df_cell['lat'] <= model_params["bounding_box"][2] + increase) 
                          & (df_cell['lon'] >= model_params["bounding_box"][1] - increase) & (df_cell['lon'] <= model_params["bounding_box"][3]) + increase]
    df_cell['Hoofdstraalrichting'] = df_cell['Hoofdstraalrichting'].str.replace('\D', '')
    df_cell['Hoofdstraalrichting'] = df_cell['Hoofdstraalrichting'].str.replace(' ', '')
    
    # Read in trajectories, limit and add seconds passed column
    df_trajectory = pd.read_csv(model_params["trajectory_file"])
    df_trajectory = df_trajectory.loc[(df_trajectory['timestamp'] >= model_params["start_date"]) & (df_trajectory['timestamp'] <= model_params["end_date"])]
    df_trajectory['seconds'] = [(datetime.strptime(x,"%Y-%m-%d %H:%M:%S") - start).total_seconds() for x in df_trajectory['timestamp']]
    all_cells = np.array(list(zip(df_cell['lat'],df_cell['lon'])))


    agents = sorted(pd.unique(df_trajectory['owner']))  
    writing_id = 0

    # loop over agents and obtain trajectory per agent
    for i in range(len(agents)):
        agents_df = df_trajectory[df_trajectory['owner'].isin([agents[i]])] 
        max = agents_df['seconds'].iloc[-1]

        # for each phone we sample from a poisson distribution with rate of one per hour
        for phone in range(2):
            index = 0
            p_time = np.random.default_rng().exponential(scale=3600)
            x_old, y_old = 0,0
            cellx, celly, degree = 0,0,0

            while(p_time <= max):
                while (agents_df['seconds'].iloc[index] < p_time):
                    index += 1
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
                agent = re.sub("[^0-9]", "", agents[i])
                if (agents_df['status'].iloc[index-1] == "transport"):
                    output_writer.writerow([writing_id, f"Agent{agent}", f"{agent}_{phone+1}", 
                                start + timedelta(seconds = p_time), cellx, celly, degree,"0-0-0"])
                
                p_time += np.random.default_rng().exponential(scale=3600)
                writing_id += 1
    output_file.close()



if __name__ == '__main__':
    model_params = {
        "start_date": START_DATE,
        "end_date": END_DATE,
        "bounding_box": BOUNDING_BOX,
        "cell_file": CELL_FILE,
        "trajectory_file": OUTPUT_TRAJECTORY_FILE,
        "output_file": OUTPUT_CELL_FILE,
    }
    main(model_params)