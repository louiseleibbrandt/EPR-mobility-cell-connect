from pathlib import Path

import pandas as pd
import folium
import branca
from branca.element import Element


## Baseline Param
data_path = Path('././outputs/trajectories2.0/Returners/Eval/output_trajectory.csv')
start_date = '2023-06-04'
end_date = '2023-06-05'

agents = ["Agent2"]

## Movers

# data_path = Path('././outputs/trajectories2.0/Movers/Eval/output_trajectory.csv')
# start_date = '2023-05-22'
# end_date = '2023-05-23'

# agents = ["Agent26"]
# data_path = Path('././outputs/trajectories2.0/Movers/Eval/output_trajectory.csv')
# start_date = '2023-05-29'
# end_date = '2023-05-30'

# agents = ["Agent26"]


## Returners Slow second better
# data_path = Path('././outputs/trajectories2.0/ReturnersSlow/Eval/output_trajectory.csv')
# start_date = '2023-05-28'
# end_date = '2023-05-29'

# agents = ["Agent13"]

# data_path = Path('././outputs/trajectories2.0/ReturnersSlow/Train/output_trajectory.csv')
# start_date = '2023-05-27'
# end_date = '2023-05-28'

# agents = ["Agent17"]

## movers slow second is better
# data_path = Path('././outputs/trajectories2.0/MoversSlow/Eval/output_trajectory.csv')
# start_date = '2023-05-26'
# end_date = '2023-05-27'

# agents = ["Agent12"]
# data_path = Path('././outputs/trajectories2.0/MoversSlow/Eval/output_trajectory.csv')
# start_date = '2023-05-10'
# end_date = '2023-05-11'

# agents = ["Agent16"]

df = pd.read_csv(data_path)

mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
df = df.loc[mask]
mask = (df['owner'].isin(agents)) 
df = df.loc[mask]


for date_col in ['timestamp']:
    df[date_col] = pd.to_datetime(df[date_col])
df = df.sort_values('timestamp')
df = df.rename(columns={"cellinfo.wgs84.lon": "longitude", "cellinfo.wgs84.lat": "latitude"})

m = folium.Map(location=(df.latitude.mean(), df.longitude.mean()),
               tiles='CartoDB positron',zoom_start=11, control_scale=True)

print(df.timestamp.min())
print(df.timestamp.max())


df['timestamp_seconds'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()

colorscale = branca.colormap.LinearColormap(
    colors=['red','yellow','green'],
    vmin=df['timestamp_seconds'].min(),
    vmax=df['timestamp_seconds'].max()
).to_step(n=200)

points = []
colors = []  # List to hold colors based on timestam
status_previous = ""
timestamp_previous = 0
lat_previous = 0
long_previous = 0
for _, report in df.iterrows():
    points.append((report.latitude, report.longitude))
    colors.append(report.timestamp_seconds)  # Use normalized timestamp for color\
    if(status_previous != "transport"):
        folium.Circle(
            location=(lat_previous, long_previous),
            fill=True,
            fill_opacity=0.5,
            radius = (report.timestamp_seconds - timestamp_previous)/100,
            color = colorscale(report.timestamp_seconds),
        ).add_to(m)
        # print(report.timestamp_seconds - timestamp_previous)
    status_previous = report.status
    timestamp_previous = report.timestamp_seconds
    lat_previous = report.latitude
    long_previous = report.longitude



folium.ColorLine(
    positions=points,
    colors=colors,  # Use the normalized timestamp values for colors
    colormap=colorscale,  # Use the defined colorscale
    weight=2.5,
    opacity=1
).add_to(m)



m.save(f'./{data_path.stem}.html')



