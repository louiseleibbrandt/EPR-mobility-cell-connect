import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import re

# Start and End date for trajectory analysis
start_date = '2023-06-01'
end_date = '2023-06-02'

df_cell = pd.read_csv('././outputs/trajectories2.0/Returners/Eval/sampling1/output_cell.csv')
df_trajectory = pd.read_csv('././outputs/trajectories2.0/Returners/Eval/output_trajectory.csv')
mask = (df_trajectory['timestamp'] >= start_date) & (df_trajectory['timestamp'] <= end_date)
df_trajectory = df_trajectory.loc[mask]

mask = (df_cell['timestamp'] >= start_date) & (df_cell['timestamp'] <= end_date)
df_cell = df_cell.loc[mask]




bounding_box1 = (4.2009,51.8561,4.5978,52.1149)

walkway_file = f"data/zuid-holland/gis_osm_roads_free_1.zip"
walkway_file_trip = f"data/noord-holland/gis_osm_roads_free_1.zip"

fig, (ax1,ax2,ax3) = plt.subplots(1,3)
walkway_df = (
            gpd.read_file(walkway_file, bounding_box1)
        )

walkway_df.plot(ax=ax1,color='black',linewidth=0.5)
walkway_df.plot(ax=ax2,color='black',linewidth=0.5)
walkway_df.plot(ax=ax3,color='black',linewidth=0.5)

agents = sorted(pd.unique(df_cell['owner']))
print(agents)

for i in range(11,21):
    agents_cell = df_cell[df_cell['owner'].isin([agents[i]])] 
    agents_trajectory = df_trajectory[df_trajectory['owner'].isin([agents[i]])] 

    lon = agents_trajectory['cellinfo.wgs84.lon']
    lat = agents_trajectory['cellinfo.wgs84.lat']
    ax1.plot(lon, lat, zorder=5,linewidth=1.5)
    ax1.scatter(lon, lat, zorder=10, s=10)
    ax1.set_title('Trajectory')

    phone1_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agents[i])+"_1"])] 
    phone2_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agents[i])+"_2"])] 


    lon1 = phone1_df['cellinfo.wgs84.lon']
    lat1 = phone1_df['cellinfo.wgs84.lat']
    lon2 = phone2_df['cellinfo.wgs84.lon']
    lat2 = phone2_df['cellinfo.wgs84.lat']

    ax2.plot(lon1, lat1, zorder=5,linewidth=1.2)
    ax2.scatter(lon1, lat1, zorder=10, s=10)
    ax2.set_title('Cell Towers: Phone 1')
    ax3.plot(lon2, lat2, zorder=5,linewidth=1.2)
    ax3.scatter(lon2, lat2, zorder=10, s=10)
    ax3.set_title('Cell Towers: Phone 2')



    

plt.show()