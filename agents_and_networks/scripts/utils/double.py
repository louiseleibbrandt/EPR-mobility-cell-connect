import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from datetime import datetime, timedelta

start_date = datetime(2023,5,1)
df_trajectory = pd.read_csv('././outputs/trajectories/output_trajectory.csv')
df_trajectory['timestamp'] = [(datetime.strptime(x,"%Y-%m-%d %H:%M:%S")-start_date)+timedelta(0) for x in df_trajectory['timestamp']]
df_trajectory['timestamp'] =  [x+x + start_date for x in df_trajectory['timestamp']] 

df_trajectory.to_csv('././outputs/trajectories/output_trajectory_double.csv')