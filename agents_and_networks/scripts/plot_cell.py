import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString
from pyproj import Transformer

import random
from math import atan2,degrees


#bounding_box = (4.3120,51.9807,4.3731,52.0239)
bounding_box = (4.3101,51.9004,4.5312,52.0354)


df = pd.read_csv('./data/20191202131001.csv')


walkway_file = "./data/zuid-holland/gis_osm_roads_free_1.zip"
df['lon'],df['lat'] =  Transformer.from_crs("EPSG:28992","EPSG:4979").transform(df['X'],df['Y'])

mask = (df['lat'] >= bounding_box[0]) & (df['lat'] <= bounding_box[2]) & (df['lon'] >= bounding_box[1]) & (df['lon'] <= bounding_box[3])
df = df.loc[mask]
df['Hoofdstraalrichting'] = df['Hoofdstraalrichting'].str.replace('\D', '')
df['Hoofdstraalrichting'] = df['Hoofdstraalrichting'].str.replace(' ', '')
# random points to check
lats = np.linspace(bounding_box[0],bounding_box[2],10)
longs = np.linspace(bounding_box[1],bounding_box[3],10)
random.shuffle(lats)
random.shuffle(longs)

closest_cell_lat = []
closest_cell_long = []
all_cells = np.array(list(zip(df['lat'],df['lon'])))


for (x,y) in zip(lats,longs):
    position = np.array((x,y))
    distances = np.linalg.norm(all_cells-position, axis=1)
    found = False

    while (not found):
        index = np.argmin(distances)
        degree_cell = df['Hoofdstraalrichting'].iloc[index]
        degree_actual = (degrees(atan2(y-all_cells[index][1], x-all_cells[index][0]))+360)%360
        if (degree_actual >= int(degree_cell) - 60 and degree_actual <= int(degree_cell) + 60):
            found = True
        else:
            distances[index] = float('inf')
        
    print("CELL",degree_cell)
    print("RELATION",degree_actual)
    closest_cell_lat.append(all_cells[index][0])
    closest_cell_long.append(all_cells[index][1])


fig, ax = plt.subplots()

walkway_df = (
            gpd.read_file(walkway_file, bounding_box)
        )
walkway_df.plot(ax=ax,color='gray')
plt.scatter(df['lat'],df['lon'],zorder=5)

# plt.scatter(lats,longs,c='red',zorder=10)
# plt.scatter(closest_cell_lat,closest_cell_long,s=10,c='orange',zorder=15)

plt.show()



