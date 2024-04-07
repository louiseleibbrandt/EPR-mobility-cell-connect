import pickle
import pandas as pd
import numpy as np
import re

import csv
from pyproj import Transformer
from datetime import datetime, timedelta
from telcell.data.models import Measurement, Point
from telcell.data.models import RDPoint
from random import choices


"""
Script to obtain the cell tower samplings from a pre-existing coverage model
"""
def main(model_params):

    # Retrieve start date
    start = datetime.strptime(model_params["start_date"],"%Y-%m-%d")

    # Setup output file
    output_file = open(model_params["output_file"], 'w')
    output_writer = csv.writer(output_file)
    output_writer.writerow(['id','owner','device','timestamp','cellinfo.wgs84.lat','cellinfo.wgs84.lon','cellinfo.azimuth_degrees','cell'])    

    # Read in cell towers: 
    df_cell = pd.read_csv(model_params["cell_file"])

    # As coverage model does not take certain information into account (such as safe distance and power) 
    # we remove this information and drop any duplicates.
    df_cell = df_cell.drop(['Samenvatting','Vermogen', 'Frequentie','Veilige afstand','id'], axis=1)
    df_cell = df_cell .drop_duplicates()

    # Only consider LTE (4G) for now
    df_cell = df_cell.loc[df_cell['HOOFDSOORT'] == "LTE"]

    # Transform to wgs84
    df_cell['lat'],df_cell['lon'] =  Transformer.from_crs("EPSG:28992","EPSG:4979").transform(df_cell['X'],df_cell['Y'])
 
    # Only keep cell towers in bounding box
    df_cell = df_cell.loc[(df_cell['lon'] >= model_params["bounding_box"][0]) & (df_cell['lon'] <= model_params["bounding_box"][2]) 
                          & (df_cell['lat'] >= model_params["bounding_box"][1]) & (df_cell['lat'] <= model_params["bounding_box"][3])]

    # drop rows that contain the partial string "Sci"
    df_cell = df_cell[~df_cell['Hoofdstraalrichting'].str.contains('|'.join(["-"]))]
    df_cell['Hoofdstraalrichting'] = df_cell['Hoofdstraalrichting'].str.replace('\D', '')
    df_cell['Hoofdstraalrichting'] = df_cell['Hoofdstraalrichting'].str.replace(' ', '')

    # Read in trajectories
    df_trajectory = pd.read_csv(model_params["trajectory_file"])

    # Limit to start and end date
    df_trajectory = df_trajectory.loc[(df_trajectory['timestamp'] >= model_params["start_date"]) & (df_trajectory['timestamp'] <= model_params["end_date"])]
    
    # Create seconds passed column for time sampling
    df_trajectory['seconds'] = [(datetime.strptime(x,"%Y-%m-%d %H:%M:%S") - start).total_seconds() for x in df_trajectory['timestamp']]
    
    # Store in list for ease of implementation
    all_cells = np.array(list(zip(df_cell['lat'],df_cell['lon'])))

    # Get unique agents
    agents = sorted(pd.unique(df_trajectory['owner']))  
    
    # Load in coverage model, we utilize the model with mnc 8 and 0 time difference
    coverage_models = pickle.load(open('././data/coverage_model', 'rb'))
    print(coverage_models)
    model = coverage_models[('16',(0, 0))]

    # Initialize variables 
    writing_id = 0
    all_grids = []
    all_degree = []
    distances_home = []

    # Read in grid with probabilites for each cell in our cell towere dataframe
    for i in range(len(all_cells)):
        grid = model.probabilities(Measurement(
                        coords=Point(lat=float(all_cells[i][0]),
                                    lon=float(all_cells[i][1])),
                        timestamp=datetime.now(),
                        extra={'mnc': '16',
                            'azimuth': df_cell['Hoofdstraalrichting'].iloc[i],
                            'antenna_id': df_cell['ID'].iloc[i],
                            'zipcode': df_cell['POSTCODE'].iloc[i],
                            'city': df_cell['WOONPLAATSNAAM'].iloc[i]}))
        # Store grids and azimuth degree for later use
        all_grids.append(grid)
        all_degree.append(df_cell['Hoofdstraalrichting'].iloc[i])

    # loop over agents and obtain trajectory per agent, store max observed time
    for i in range(len(agents)):
        agents_df = df_trajectory[df_trajectory['owner'].isin([agents[i]])] 
        max = agents_df['seconds'].iloc[-1]
        
        print("Agents",i)
        
        # if we do independent sampling then we want to do full sampling twice for each phone
        # else we do the sampling once and utilize switch
        samples = 1
        if (model_params["sampling_method"] == 1):
            samples = 2
        
        # if we do location based sampling, we keep track of 
        if (model_params["sampling_method"] == 3):
            X = np.array(list(zip(agents_df['cellinfo.wgs84.lat'],agents_df['cellinfo.wgs84.lon'])))    
            home_loc = agents_df.loc[agents_df['status'] == 'home']
            home = (home_loc['cellinfo.wgs84.lat'].iloc[0],home_loc['cellinfo.wgs84.lon'].iloc[0])
            distances_home = np.linalg.norm(X-np.array((home[0],home[1])), axis=1)

        # for each phone we sample from a poisson distribution with rate of one per hour
        for phone in range(samples):
            p_time = np.random.default_rng().exponential(scale=3600)
            index = 0
            x_old, y_old = 0, 0
            index_cell = 0
            while(p_time <= max):
                while (agents_df['seconds'].iloc[index] < p_time):
                    index += 1
                x = agents_df['cellinfo.wgs84.lat'].iloc[index-1]
                y = agents_df['cellinfo.wgs84.lon'].iloc[index-1]
                rd = Point(lat = x,lon = y).convert_to_rd()
                
                if (x_old != round(rd.x/100)*100 or y_old != round(rd.y/100)*100):
                    probabilities = [grid.get_value_for_coord(RDPoint(x=rd.x,y = rd.y)) for grid in all_grids]

                index_cell = choices(list(range(len(probabilities))), weights = probabilities)[0]
                x_old = round(rd.x/100)*100
                y_old = round(rd.y/100)*100


                agent = re.sub("[^0-9]", "", agents[i])
                if (model_params["sampling_method"] == 2):
                    day_time = p_time%86400
                    if (day_time >= 32400 and day_time <= 61200):
                        phone = 1
                    else:
                        phone = 0
                    
                elif (model_params["sampling_method"] == 3):
                    if(distances_home[index-1] > 0.05):
                        phone = 1
                    else:
                        phone = 0
       
                output_writer.writerow([writing_id, f"Agent{agent}", f"{agent}_{phone+1}", 
                                    start + timedelta(seconds = p_time), all_cells[index_cell][0], all_cells[index_cell][1], all_degree[index_cell],"0-0-0"])
                
                p_time += np.random.default_rng().exponential(scale=3600)
                writing_id += 1

    output_file.close()



if __name__ == '__main__':
    model_params = {
        "start_date": '2023-05-10',
        "end_date": '2023-06-10',
        "bounding_box":(4.2009,51.8561,4.5978,52.1149),
        "cell_file": './data/20191202131001.csv',
        "trajectory_file": '././outputs/trajectories2.0/Returners/Train/output_trajectory.csv',
        "output_file": '././outputs/trajectories2.0/Returners/Train/sampling1/output_cell.csv',
        # 1 for independent sampling, 2 for dependent on time and 3 for dependent on location
        "sampling_method": 1
    }
    main(model_params)

