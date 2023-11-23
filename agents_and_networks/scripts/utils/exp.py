
import pandas as pd
import re

start_date = '2023-07-01'
end_date = '2023-07-31'

df_cell = pd.read_csv('./outputs/trajectories/Final_Eval/Explorer/output_cell.csv')

mask = (df_cell['timestamp'] >= start_date) & (df_cell['timestamp'] <= end_date)
df_cell = df_cell.loc[mask]

output_file = open('./outputs/trajectories/Final_Eval/Explorer/output_cell_small.csv', 'w')


df_cell.to_csv(output_file, mode='a', index=False, header=True)


# start_date = '2023-07-01'
# end_date = '2023-07-31'

# df_trajectory200 = pd.read_csv('./outputs/trajectories/Final_Train/Returner/output_trajectory200.csv')
# df_trajectory100 = pd.read_csv('./outputs/trajectories/Final_Train/Returner/output_trajectory100.csv')
# output_file = open('./outputs/trajectories/Final_Train/Returner/output_trajectory300.csv', 'w')

# df_trajectory100['owner'] =  df_trajectory100['owner'].apply(lambda x: f'Agent{int(re.sub("[^0-9]", "", x))+200}')
# df_trajectory100['id'] =  df_trajectory100['id'].apply(lambda x: x+len(df_trajectory200))
# df_trajectory300 = pd.concat([df_trajectory200,df_trajectory100])


# df_trajectory300.to_csv(output_file, mode='a', index=False, header=True)
