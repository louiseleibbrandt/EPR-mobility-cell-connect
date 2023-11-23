import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import re
import numpy as np
import csv


def get_overlapping(matrix,agents,least,output_number) -> list:
    overlapping = []
    matrixc = matrix.copy()
    agents = np.array(agents)
    if least:
        arg = np.argmin(np.sum(matrixc, 1))
    else:
        arg = np.argmax(matrixc.sum(axis=1))
        
    total = matrixc[arg]
    overlapping.append(agents[arg])

    matrixc[arg,:] = 1 if least else 0

    while(len(overlapping) < output_number):
        mult = np.multiply(matrixc,total)
        if least:
            arg = np.argmin(np.sum(mult, 1))
        else:
            arg = np.argmax(np.sum(mult, 1))
        print(arg)
        total = np.add(matrixc[arg],total)
        overlapping.append(agents[arg])
        matrixc[arg,:] = 1 if least else 0
    return overlapping

def plot_results(model_params,overlap,df_cell,df_trajectory) -> None:
    fig, (ax1,ax2,ax3) = plt.subplots(1,3)
    walkway_df = (
                gpd.read_file(model_params["walkway_file"], model_params["bounding_box"])
            )
    walkway_df.plot(ax=ax1,color='black')
    walkway_df.plot(ax=ax2,color='black')
    walkway_df.plot(ax=ax3,color='black')   
            
    for agent in overlap:
        agents_cell = df_cell[df_cell['owner'].isin([agent])] 
        agents_trajectory = df_trajectory[df_trajectory['owner'].isin([agent])] 

        lon = agents_trajectory['cellinfo.wgs84.lon']
        lat = agents_trajectory['cellinfo.wgs84.lat']
        ax1.plot(lon, lat,zorder=5)
        ax1.scatter(lon, lat,zorder=10)
        ax1.set_title('Trajectory')

        phone1_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agent)+"_1"])] 
        phone2_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agent)+"_1"])] 


        lon1 = phone1_df['cellinfo.wgs84.lon']
        lat1 = phone1_df['cellinfo.wgs84.lat']
        lon2 = phone2_df['cellinfo.wgs84.lon']
        lat2 = phone2_df['cellinfo.wgs84.lat']

        ax2.plot(lon1, lat1,zorder=5)
        ax2.scatter(lon1, lat1,zorder=10)
        ax2.set_title('Cell Towers: Phone 1')
        ax3.plot(lon2, lat2,zorder=5)
        ax3.scatter(lon2, lat2,zorder=10)
        ax3.set_title('Cell Towers: Phone 2')

    plt.show()

def write_to_file(model_params,overlap,df_cell,df_trajectory,obj) -> None:
    if obj == 0: 
        output_file_trajectory = open(f"{model_params['output_file_no_overlap']}/output_trajectory.csv", 'w')
        output_file_cell = open(f"{model_params['output_file_no_overlap']}/output_cell.csv", 'w')
    elif obj == 1:
        output_file_trajectory = open(f"{model_params['output_file_overlap']}/output_trajectory.csv", 'w')
        output_file_cell= open(f"{model_params['output_file_overlap']}/output_cell.csv", 'w')
    else:
        output_file_trajectory = open(f"{model_params['output_file_combined']}/output_trajectory.csv", 'w')
        output_file_cell = open(f"{model_params['output_file_combined']}/output_cell.csv", 'w')

    output_writer_trajectory = csv.writer(output_file_trajectory)
    output_writer_cell = csv.writer(output_file_cell)

    output_writer_trajectory.writerow(['id','owner','timestamp','cellinfo.wgs84.lon','cellinfo.wgs84.lat'])     
    output_writer_cell.writerow(['id','owner','device','timestamp','cellinfo.wgs84.lon','cellinfo.wgs84.lat','cellinfo.azimuth_degrees','cell'])     

    for agent in overlap:
        agents_trajectory = df_trajectory[df_trajectory['owner'].isin([agent])] 
        agents_cell = df_cell[df_cell['owner'].isin([agent])] 
        phone1_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agent)+"_1"])] 
        phone2_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agent)+"_2"])] 
        lon1 = pd.unique(phone1_df['cellinfo.wgs84.lon'])
        lon2 = pd.unique(phone2_df['cellinfo.wgs84.lon'])
        if (len(lon1) > 1 and len(lon2) > 1):
            agents_trajectory.to_csv(output_file_trajectory, mode='a', index=False, header=False)
            agents_cell.to_csv(output_file_cell, mode='a', index=False, header=False)

def main(model_params):
    df_cell = pd.read_csv(model_params["cell_file"])
    df_trajectory = pd.read_csv(model_params["trajectory_file"])
 
    df_cell = df_cell.loc[(df_cell['timestamp'] >= model_params["start_date"]) & (df_cell['timestamp'] <= model_params["end_date"])]
    df_trajectory = df_trajectory.loc[(df_trajectory['timestamp'] >= model_params["start_date"]) & (df_trajectory['timestamp'] <= model_params["end_date"])]

    agents = sorted(pd.unique(df_cell['owner']))
    matrix = np.loadtxt(model_params["text_file"], usecols=range(len(agents)))

    no_overlap = get_overlapping(matrix, agents, True, model_params["output_numer"])
    write_to_file(model_params, no_overlap, df_cell,df_trajectory, 0)
    

    overlap = get_overlapping(matrix, agents, False, model_params["output_numer"])
    write_to_file(model_params, overlap, df_cell, df_trajectory, 1)
    
    write_to_file(model_params, no_overlap+overlap, df_cell, df_trajectory, 2)



if __name__ == '__main__':
    model_params = {
        "start_date": '2023-07-01',
        "end_date": '2023-07-31',
        "bounding_box":(4.3739,51.8451,4.5786,51.9623),
        "cell_file": './outputs/trajectories/Final_Eval/Returner/output_cell200.csv',
        "trajectory_file": './outputs/trajectories/Final_Eval/Returner/output_trajectory200.csv',
        "text_file": './outputs/trajectories/Final_Eval/Returner/outfile200.txt',
        "walkway_file":'./data/zuid-holland/gis_osm_roads_free_1.zip',
        "output_file_no_overlap":'./outputs/trajectories/Final_Eval/Returner/no_overlap',
        "output_file_overlap":'./outputs/trajectories/Final_Eval/Returner/overlap',
        "output_file_combined":'./outputs/trajectories/Final_Eval/Returner/combined',
        "output_numer": 50,
    }
    main(model_params)