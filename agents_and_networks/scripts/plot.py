import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString
from pyproj import Transformer

df = pd.read_csv('./outputs/trajectories/output_trajectory.csv')
#df = pd.read_csv('./outputs/trajectories/output_cell.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# filter dataframe by date
start_date = '2023-05-01'
end_date = '2023-05-15'
mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
df = df.loc[mask]
# bounding_box = (4.3120,51.9807,4.3731,52.0239)
#bounding_box = (4.3101,51.9004,4.5312,52.0354)
bounding_box = (4.2009,51.8561,4.5978,52.1149)
walkway_file = "./data/zuid-holland/gis_osm_roads_free_1.zip"

#"epsg:3857"


colors = ['red','salmon','blue','royalblue', 'green','lightgreen','orange','bisque','purple','plum',
          'red','salmon','blue','royalblue', 'green','lightgreen','orange','bisque','purple','plum',
          'red','salmon','blue','royalblue', 'green','lightgreen','orange','bisque','purple','plum',
          'red','salmon','blue','royalblue', 'green','lightgreen','orange','bisque','purple','plum']

agents = sorted(pd.unique(df['owner']))

fig, ax = plt.subplots()
walkway_df = (
            gpd.read_file(walkway_file, bounding_box)
        )
walkway_df.plot(ax=ax,color='gray')

for i in range(len(agents)):
    agents_df = df[df['owner'].isin([agents[i]])] 
    # phone2_df = agents_df[agents_df['device'].isin([chr(i+65)+"_1"])] 
    # phone1_df = agents_df[agents_df['device'].isin([chr(i+65)+"_2"])] 
    lon = agents_df['cellinfo.wgs84.lon']
    lat = agents_df['cellinfo.wgs84.lat']
    
    # lon1 = phone1_df['cellinfo.wgs84.lon']
    # lat1 = phone1_df['cellinfo.wgs84.lat']
    # lon2 = phone2_df['cellinfo.wgs84.lon']
    # lat2 = phone2_df['cellinfo.wgs84.lat']
    # print(colors[2*i-1])
    # plt.plot(lon1, lat1,color=colors[2*i+1],zorder=5)
    # plt.scatter(lon1, lat1,color=colors[2*i+1],zorder=10)
    # print(colors[2*i])
    # plt.plot(lon2, lat2,color=colors[2*i],zorder=5)
    # plt.scatter(lon2, lat2,color=colors[2*i],zorder=10)
    plt.plot(lon, lat,zorder=5)
    plt.scatter(lon, lat,zorder=10)

plt.show()