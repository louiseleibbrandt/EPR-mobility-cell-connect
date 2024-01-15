from pathlib import Path

import pandas as pd
import folium
import branca

data_path = Path('././outputs/trajectories/Location_Eval/Time_Sampling2/Random_Work/output_cell.csv')
start_date = '2023-06-01'
end_date = '2023-06-30'

df = pd.read_csv(data_path)

mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
df = df.loc[mask]
mask = (df['owner'] == 'Agent1')
df = df.loc[mask]


mask = (df['device'] == '8_2')
df = df.loc[mask]

for date_col in ['timestamp']:
    df[date_col] = pd.to_datetime(df[date_col])
df = df.sort_values('timestamp')
df = df.rename(columns={"cellinfo.wgs84.lon": "longitude", "cellinfo.wgs84.lat": "latitude"})

m = folium.Map(location=(df.latitude.mean(), df.longitude.mean()),
               tiles='CartoDB positron')
colorscale = branca.colormap.linear.viridis.scale(df.timestamp.min(),
                                                  df.timestamp.max())
colorscale.caption = "Scaled report date"

points = []
for _, report in df.iterrows():
    report_html = report.to_frame().to_html(header=False)
    points.append(tuple([report.latitude, report.longitude]))
    folium.Circle(
        location=(report.latitude, report.longitude),
        fill=True,
        fill_opacity=0.1,
        popup=folium.Popup(html=report_html,
                           max_width=600),
        tooltip=folium.Tooltip(report_html),
    ).add_to(m)
    

folium.PolyLine(points, color="blue", weight=2.5, opacity=0.1).add_to(m)

southwest = df[['latitude', 'longitude']].min().values.tolist()
northeast = df[['latitude', 'longitude']].max().values.tolist()

m.fit_bounds([southwest, northeast])

m.save(f'./{data_path.stem}.html')
