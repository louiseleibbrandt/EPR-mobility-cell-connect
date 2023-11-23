import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import re

# Start and End date for trajectory analysis
start_date = '2023-07-01'
end_date = '2023-07-31'

df_cell = pd.read_csv('./outputs/trajectories/Final_Eval/Returner/combined/output_cell.csv')
df_trajectory = pd.read_csv('./outputs/trajectories/Final_Eval/Returner/combined/output_trajectory.csv')
mask = (df_trajectory['timestamp'] >= start_date) & (df_trajectory['timestamp'] <= end_date)
df_trajectory = df_trajectory.loc[mask]

mask = (df_cell['timestamp'] >= start_date) & (df_cell['timestamp'] <= end_date)
df_cell = df_cell.loc[mask]

# df_cell['timestamp'] = pd.to_datetime(df_cell['timestamp'])
# df_trajectory['timestamp'] = pd.to_datetime(df_trajectory['timestamp'])

# bounding_box = (4.2009,51.8561,4.5978,52.1149)
bounding_box = (4.3739,51.8451,4.5786,51.9623)
# bounding_box = (4.2648,51.8073,4.4155,51.8877)
walkway_file = "./data/zuid-holland/gis_osm_roads_free_1.zip"

fig, (ax1,ax2,ax3) = plt.subplots(1,3)
walkway_df = (
            gpd.read_file(walkway_file, bounding_box)
        )
walkway_df.plot(ax=ax1,color='black')
walkway_df.plot(ax=ax2,color='black')
walkway_df.plot(ax=ax3,color='black')

agents = sorted(pd.unique(df_trajectory['owner']))
# colors = ['blue','red','royalblue','blue','lightgreen','green','bisque','orange','plum','purple',
        #   'red','salmon','blue','royalblue', 'green','lightgreen','orange','bisque','purple','plum',
        #   'red','salmon','blue','royalblue', 'green','lightgreen','orange','bisque','purple','plum',
        #   'red','salmon','blue','royalblue', 'green','lightgreen','orange','bisque','purple','plum']
# for i, agent in enumerate( ["Agent49", "Agent79","Agent108","Agent9","Agent147","Agent90","Agent104","Agent44","Agent28","Agent9"]):
for i in range(len(agents)):
    agents_cell = df_cell[df_cell['owner'].isin([agents[i]])] 
    agents_trajectory = df_trajectory[df_trajectory['owner'].isin([agents[i]])] 

    lon = agents_trajectory['cellinfo.wgs84.lon']
    lat = agents_trajectory['cellinfo.wgs84.lat']
    ax1.plot(lon, lat, zorder=5)
    ax1.scatter(lon, lat, zorder=10)
    ax1.set_title('Trajectory')

    phone1_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agents[i])+"_1"])] 
    phone2_df = agents_cell[agents_cell['device'].isin([re.sub("[^0-9]", "", agents[i])+"_2"])] 


    lon1 = phone1_df['cellinfo.wgs84.lon']
    lat1 = phone1_df['cellinfo.wgs84.lat']
    lon2 = phone2_df['cellinfo.wgs84.lon']
    lat2 = phone2_df['cellinfo.wgs84.lat']

    ax2.plot(lon1, lat1, zorder=5)
    ax2.scatter(lon1, lat1, zorder=10)
    ax2.set_title('Cell Towers: Phone 1')
    ax3.plot(lon2, lat2, zorder=5)
    ax3.scatter(lon2, lat2, zorder=10)
    ax3.set_title('Cell Towers: Phone 2')
    # ax2.scatter(4.54759083507109,51.91984112175754, color='green', zorder=15)
    # ax2.scatter(4.545076142297967,51.94543180686215,  color='green', zorder=15)
    # ax3.scatter(4.54759083507109,51.91984112175754,  color='green', zorder=15)
    # ax3.scatter(4.545076142297967, 51.94543180686215, color='green', zorder=15)

    # ax2.scatter(4.4783047734744965, 51.876188698431655, color='green', zorder=15)
    # ax2.scatter(4.497211695837924, 51.88507954452394, color='green', zorder=15)
    # ax3.scatter(4.4783047734744965, 51.876188698431655, color='green', zorder=15)
    # ax3.scatter(4.497211695837924, 51.88507954452394, color='green', zorder=15)



    

plt.show()