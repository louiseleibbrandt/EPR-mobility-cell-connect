import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

df_cell = pd.read_csv('./outputs/trajectories/output_cell.csv')
df_trajectory = pd.read_csv('./outputs/trajectories/output_trajectory.csv')

df_cell['timestamp'] = pd.to_datetime(df_cell['timestamp'])
df_trajectory['timestamp'] = pd.to_datetime(df_trajectory['timestamp'])

bounding_box = (4.2009,51.8561,4.5978,52.1149)

walkway_file = "./data/zuid-holland/gis_osm_roads_free_1.zip"

fig, (ax1,ax2,ax3) = plt.subplots(1,3)
walkway_df = (
            gpd.read_file(walkway_file, bounding_box)
        )
walkway_df.plot(ax=ax1,color='black')
walkway_df.plot(ax=ax2,color='black')
walkway_df.plot(ax=ax3,color='black')

agents = sorted(pd.unique(df_trajectory['owner']))

for i in range(len(agents)):
    agents_cell = df_cell[df_cell['owner'].isin([agents[i]])] 
    agents_trajectory = df_trajectory[df_trajectory['owner'].isin([agents[i]])] 

    lon = agents_trajectory['cellinfo.wgs84.lon']
    lat = agents_trajectory['cellinfo.wgs84.lat']
    ax1.plot(lon, lat,zorder=5)
    ax1.scatter(lon, lat,zorder=10)
    ax1.set_title('Trajectory')

    phone1_df = agents_cell[agents_cell['device'].isin([str(i)+"_2"])] 
    phone2_df = agents_cell[agents_cell['device'].isin([str(i)+"_1"])] 
    
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