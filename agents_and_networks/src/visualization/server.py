import mesa

from src.agent.building import Building
from src.agent.commuter import Commuter
from src.agent.geo_agents import Driveway, Walkway, Path


class ClockElement(mesa.visualization.TextElement):
    def __init__(self):
        super().__init__()
        pass

    def render(self, model):
        return f"Day {model.day}, {model.hour:02d}:{model.minute:02d}"


def agent_draw(agent):
    portrayal = {}
    portrayal["color"] = "White"
    if isinstance(agent, Driveway):
        portrayal["color"] = "#D08004"
    elif isinstance(agent, Path):
        portrayal["color"] = "Brown"
    elif isinstance(agent, Walkway):
        portrayal["color"] = "#04D0CD"
    elif isinstance(agent, Building):
        # if agent.visited:
        #     if agent.function == 1:
        #         portrayal["color"] = "Blue"
        #     elif agent.function == 2:
        #         portrayal["color"] = "Green"
        #     else:
        #         portrayal["color"] = "Red"
        # else:
        portrayal["opacity"] = 0
    elif isinstance(agent, Commuter):
        if agent.status == "home":
            portrayal["color"] = "Green"
        elif agent.status == "work":
            portrayal["color"] = "Blue"
        elif agent.status == "transport":
            portrayal["color"] = "Red"
        else:
            portrayal["color"] = "Grey"
        portrayal["radius"] = "5"
        portrayal["fillOpacity"] = 1
    return portrayal


clock_element = ClockElement()
status_chart = mesa.visualization.ChartModule(
    [
        {"Label": "status_traveling", "Color": "Red"},
        {"Label": "state_explore", "Color": "Blue"},
        {"Label": "state_return", "Color": "Green"},
    ],
    data_collector_name="datacollector",
)

location_chart = mesa.visualization.ChartModule(
    [
        {"Label": "average_visited_locations", "Color": "Red"},
    ],
    data_collector_name="datacollector",

)

