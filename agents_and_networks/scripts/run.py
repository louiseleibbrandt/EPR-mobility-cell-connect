import argparse

import mesa
import mesa_geo as mg
from src.model.model import AgentsAndNetworks
from src.visualization.server import (
    agent_draw,
    clock_element,
    status_chart,
    location_chart,
)


if __name__ == "__main__":
    region_params = {
        "data_crs": "epsg:4326", "commuter_speed": 1.4
    }



    model_params = {
        "data_crs": region_params["data_crs"],
        "show_walkway": False,
        "building_source_types": ["apartments","house","allotment_house"],
        "building_destination_types": ["industrial","school","construction"],
        "bounding_box": (4.3101,51.9004,4.5312,52.0354),
        #"bounding_box":(4.3120,51.9807,4.3731,52.0239),
        "num_commuters": mesa.visualization.Slider(
            "Number of Commuters", value=18, min_value=1, max_value=150, step=10
        ),
        "commuter_speed": mesa.visualization.Slider(
            "Commuter Walking Speed (m/s)",
            value=region_params["commuter_speed"],
            min_value=0.1,
            max_value=1.5,
            step=0.1,
        ),
        "step_duration": mesa.visualization.NumberInput(
            "Step Duration (seconds)",
            value=10,
        ),
        "alpha": mesa.visualization.NumberInput(
            "Exponent jump size distribution (truncated power law)",
            value=0.55,
        ),
        "tau_jump": mesa.visualization.NumberInput(
            "Max jump (km) jump size distribution (truncated power law)",
            value=100.0,
        ),
        "beta": mesa.visualization.NumberInput(
            "Exponent waiting time distribution (truncated power law)",
            value=0.8,
        ),
        "tau_time": mesa.visualization.NumberInput(
            "Max time (hour) waiting time distribution (truncated power law)",
            value=10,
        ),
        "rho": mesa.visualization.NumberInput(
            "Constant in probability of exploration",
            value=0.5,
        ),
        "gamma": mesa.visualization.NumberInput(
            "Exponent in probability of exploration",
            value=2.0,
        ),
        "buildings_file": f"data/zuid-holland/gis_osm_buildings_a_free_1.zip",
        "walkway_file": f"data/zuid-holland/gis_osm_roads_free_1.zip",
        "celltower_file": f"data/20191202131001.csv",
    }

    map_element = mg.visualization.MapModule(agent_draw, map_height=600, map_width=600)
    server = mesa.visualization.ModularServer(
        AgentsAndNetworks,
        #[map_element, clock_element, status_chart, location_chart],
        [clock_element],
        "Agents and Networks",
        model_params,
    )
    server.launch()
