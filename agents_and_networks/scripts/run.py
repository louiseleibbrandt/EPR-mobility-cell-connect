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
        "start_date": '2023-05-01',
        "bounding_box":(4.2009,51.8561,4.5978,52.1149),
        "bounding_box_trip":(4.8582,52.3478,4.9423,52.3926),
        # "bounding_box_festival":(4.8512,52.3933,4.8626,52.3988),
        "num_commuters": mesa.visualization.Slider(
            "Number of Commuters", value=100, min_value=1, max_value=150, step=10
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
            value=60,
        ),
        "allow_trips": mesa.visualization.Checkbox(
            "Allow Trips",
            value=True,
        ),
        "only_same_day_trips": mesa.visualization.Checkbox(
            "Trips Occur on the Same Day",
            value=True,
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
            value=17,
        ),
        "rho": mesa.visualization.NumberInput(
            "Constant in probability of exploration",
            value=1,
        ),
        "gamma": mesa.visualization.NumberInput(
            "Exponent in probability of exploration",
            value=2,
        ),
        "buildings_file": f"data/zuid-holland/gis_osm_buildings_a_free_1.zip",
        "buildings_file_trip": f"data/noord-holland/gis_osm_buildings_a_free_1.zip",
        "walkway_file": f"data/zuid-holland/gis_osm_roads_free_1",
        "walkway_file_trip": f"data/noord-holland/gis_osm_roads_free_1",
    }

    map_element = mg.visualization.MapModule(agent_draw, map_height=600, map_width=600)
    server = mesa.visualization.ModularServer(
        AgentsAndNetworks,
        # [map_element, clock_element],
        [clock_element],
        "Agents and Networks",
        model_params,
    )
    server.launch()
