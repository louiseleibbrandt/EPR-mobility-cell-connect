# config.py
# Bounding box for trajectory simulation 
BOUNDING_BOX = (4.3480,52.0036,4.3741,52.0185)
# Bounding box increase for connecting cell tower simulation
BOUNDING_INCREASE = 0.01

# Start and end date of simulation
START_DATE = '2023-05-01'
END_DATE = '2023-06-10'

# Cell tower location file and pickled coverage model
CELL_FILE = 'data/20191202131001.csv'
COVERAGE_FILE = 'data/coverage_model'

# Locations for output trajectory and cell tower connections
OUTPUT_TRAJECTORY_FILE = 'outputs/output_trajectory.csv'
OUTPUT_CELL_FILE = 'outputs/output_cell.csv'

# Building file and street file
# Download regions from following location https://download.geofabrik.de/europe/netherlands.html
BUILDING_FILE = 'data/zuid-holland/gis_osm_buildings_a_free_1.zip'
STREET_FILE = 'data/zuid-holland/gis_osm_roads_free_1.zip'
