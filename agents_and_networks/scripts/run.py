import mesa
import mesa_geo as mg
from config import BOUNDING_BOX, START_DATE, BUILDING_FILE, STREET_FILE, OUTPUT_TRAJECTORY_FILE
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
        "start_date": START_DATE,
        "bounding_box":BOUNDING_BOX,
        "num_commuters": mesa.visualization.NumberInput(
            "Number of agents",
            value=10,
        ),
        "commuter_speed_walk": mesa.visualization.NumberInput(
            "Agent moving speed (m/s)",
            value=region_params["commuter_speed"],
        ),
        "step_duration": mesa.visualization.NumberInput(
            "Step duration (seconds)",
            value=60,
        ),
        "alpha": mesa.visualization.NumberInput(
            "Exponent travel distance distribution (truncated power law)",
            value=0.55,
        ),
        "tau_jump_min": mesa.visualization.NumberInput(
            "Min travel distance (km)",
            value=1.0,
        ),
        "tau_jump": mesa.visualization.NumberInput(
            "Max travel distance (km)",
            value=100.0,
        ),
        "beta": mesa.visualization.NumberInput(
            "Exponent waiting time distribution (truncated power law)",
            value=0.8,
        ),
        "tau_time_min": mesa.visualization.NumberInput(
            "Min waiting time (hour)",
            value=0.33,
        ),
        "tau_time": mesa.visualization.NumberInput(
            "Max waiting time (hour)",
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
        "buildings_file": BUILDING_FILE,
        "walkway_file": STREET_FILE,
        "output_file": OUTPUT_TRAJECTORY_FILE,
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
