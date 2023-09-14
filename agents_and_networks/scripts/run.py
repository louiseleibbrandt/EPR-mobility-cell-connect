import argparse

import mesa
import mesa_geo as mg
from src.model.model import AgentsAndNetworks
from src.visualization.server import (
    agent_draw,
    clock_element,
    status_chart,
)


def make_parser():
    parser = argparse.ArgumentParser("Agents and Networks in Python")
    parser.add_argument("--region", type=str, required=True)
    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()

    if args.region == "zuid-holland":
        data_file_prefix = "zuid-holland"
    else:
        raise ValueError("Invalid campus name. Choose from ub or gmu.")
    
    region_params = {
        "zuid-holland": {"data_crs": "epsg:4326", "commuter_speed": 0.5},
    }



    model_params = {
        "region": args.region,
        "data_crs": region_params[args.region]["data_crs"],
        "show_walkway": True,
        "show_lakes_and_rivers": False,
        "show_driveway": True,
        "num_commuters": mesa.visualization.Slider(
            "Number of Commuters", value=50, min_value=10, max_value=150, step=10
        ),
        "step_duration": mesa.visualization.NumberInput(
            "Step Duration (m)",
            value=5,
        ),
        "commuter_speed": mesa.visualization.Slider(
            "Commuter Walking Speed (m/s)",
            value=region_params[args.region]["commuter_speed"],
            min_value=0.1,
            max_value=1.5,
            step=0.1,
        ),
        "buildings_file": f"data/{args.region}/gis_osm_pois_a_free_1.zip",
        "walkway_file": f"data/{args.region}/gis_osm_railways_free_1.zip",
        "lakes_file": f"data/{args.region}/gis_osm_water_a_free_1.zip",
        "rivers_file": f"data/{args.region}/gis_osm_waterways_a_free_1.zip",
        "driveway_file": f"data/{args.region}/gis_osm_railways_free_1.zip",
    }

    map_element = mg.visualization.MapModule(agent_draw, map_height=600, map_width=600)
    server = mesa.visualization.ModularServer(
        AgentsAndNetworks,
        [map_element, clock_element, status_chart],
        "Agents and Networks",
        model_params,
    )
    server.launch()
ß