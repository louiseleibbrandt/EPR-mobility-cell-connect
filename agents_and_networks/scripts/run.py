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
        "bounding_box":(4.3480,52.0036,4.3741,52.0185),
        "num_commuters": mesa.visualization.NumberInput(
            "Number of Agents",
            value=10,
        ),
        "commuter_speed_walk": mesa.visualization.NumberInput(
            "Commuter Walking Speed (m/s)",
            value=region_params["commuter_speed"],
        ),
        "step_duration": mesa.visualization.NumberInput(
            "Step Duration (seconds)",
            value=60,
        ),
        "alpha": mesa.visualization.NumberInput(
            "Exponent jump size distribution (truncated power law)",
            value=0.55,
        ),
        "tau_jump_min": mesa.visualization.NumberInput(
            "Min jump (km) jump size distribution",
            value=1.0,
        ),
        "tau_jump": mesa.visualization.NumberInput(
            "Max jump (km) jump size distribution",
            value=100.0,
        ),
        "beta": mesa.visualization.NumberInput(
            "Exponent waiting time distribution (truncated power law)",
            value=0.8,
        ),
        "tau_time_min": mesa.visualization.NumberInput(
            "Min time (hour) waiting time distribution",
            value=0.33,
        ),
        "tau_time": mesa.visualization.NumberInput(
            "Max time (hour) waiting time distribution",
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
        "walkway_file": f"data/zuid-holland/gis_osm_roads_free_1.zip",
        "output_file":f"././outputs/trajectories/output_trajectory.csv",
    }

    map_element = mg.visualization.MapModule(agent_draw, map_height=600, map_width=600)
    server = mesa.visualization.ModularServer(
        AgentsAndNetworks,
        # use following if you want map functionality
        [map_element, clock_element],
        # [clock_element],
        "Mesa Mobility extended with EPR",
        model_params,
    )
    server.launch()
