
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from src.space.utils import power_law_exponential_cutoff
import scipy.stats as stats


start_date = '2023-06-01'
end_date = '2023-06-31'

df_cell = pd.read_csv('././outputs/trajectories/Explorers/Eval/output_trajectory.csv')

mask = (df_cell['timestamp'] >= start_date) & (df_cell['timestamp'] <= end_date)
df_cell = df_cell.loc[mask]

df_cell.to_csv('././outputs/trajectories/Explorers/Eval/output_trajectory_small.csv')
# y_time1 = 0
# y1 = []

# y_time2 = 0
# y2 = []
# for i in range(30):
#     y_time1 += np.random.default_rng().exponential(scale=1)
#     y1.append(y_time1)
#     y_time2 += np.random.default_rng().exponential(scale=1)
#     y2.append(y_time2)

# x1 = [1]*30
# x2 = [2]*30
# plt.scatter(y1,x1, c='blue') 
# plt.scatter(y2,x2, c='red')
# plt.show()

# times = []
# distances = []


# for i in range(1000):
#     times.append((power_law_exponential_cutoff(2/60, 1.7, 0.8, 1.7))*60)
#     # distances.append((power_law_exponential_cutoff(1, 100, 0.55, 100)))
#     # times.append(power_law_exponential_cutoff(1/60, 1, 1, 1))*60



# plt.hist(times) 
# plt.show()
