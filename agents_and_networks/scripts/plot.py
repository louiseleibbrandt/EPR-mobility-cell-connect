import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df = pd.read_csv('./outputs/trajectories/output1.csv')
fig, ax = plt.subplots()
gdf = []
for i in range(5):
    df['geometry'+str(i)] = df.apply(lambda row: Point(row[i].strip("()").split(",")[0], row[i].strip("()").split(",")[1]), axis=1)
    gdf.append(gpd.GeoDataFrame(df, geometry='geometry'+str(i)))



gdf[0].plot(ax=ax, color='blue')
gdf[1].plot(ax=ax, color='green')
gdf[2].plot(ax=ax, color='red')
gdf[3].plot(ax=ax, color='orange')
gdf[4].plot(ax=ax, color='purple')
plt.show()
