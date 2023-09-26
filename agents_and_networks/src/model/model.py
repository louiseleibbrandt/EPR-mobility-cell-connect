import uuid
from functools import partial

import geopandas as gpd
import mesa
import mesa_geo as mg
import pandas as pd
from shapely.geometry import Point

from src.agent.building import Building
from src.agent.commuter import Commuter
from src.agent.geo_agents import Walkway
from src.space.campus import Campus
from src.space.road_network import CampusWalkway
from shapely.geometry import Point


def get_time(model) -> pd.Timedelta:
    return pd.Timedelta(days=model.day, hours=model.hour, minutes=model.minute)


def get_num_commuters_by_status(model, status: str) -> int:
    commuters = [
        commuter for commuter in model.schedule.agents if commuter.status == status
    ]
    return len(commuters)

def get_num_commuters_by_state(model, state: str) -> int:
    commuters = [
        commuter for commuter in model.schedule.agents if commuter.state == state
    ]
    return len(commuters)

def get_average_visited_locations(model) -> int:
    commuters = [
        commuter.S for commuter in model.schedule.agents 
    ]
    return sum(commuters)/len(commuters)

def get_visited_locations(model) -> list:
    commuters = [
        commuter.S for commuter in model.schedule.agents 
    ]
    return commuters


def get_pos_commuter(model) -> list:
    commuters = [
        (commuter,commuter.my_path[commuter.step_in_path]) for commuter in model.schedule.agents 
    ]
    return commuters





class AgentsAndNetworks(mesa.Model):
    running: bool
    schedule: mesa.time.RandomActivation
    show_walkway: bool
    current_id: int
    space: Campus
    walkway: CampusWalkway
    world_size: gpd.geodataframe.GeoDataFrame
    got_to_destination: int  # count the total number of arrivals
    building_source_types: list
    building_destination_types: list
    bounding_box:list
    num_commuters: int
    step_duration: int
    alpha: float
    tau_jump: float    # in meters
    beta: float
    tau_time: float    # in hours
    rho: float
    gamma: float
    day: int
    hour: int
    minute: int
    datacollector: mesa.DataCollector

    def __init__(
        self,
        region: str,
        data_crs: str,
        buildings_file: str,
        walkway_file: str,
        num_commuters,
        step_duration,
        alpha,
        tau_jump,   # in meters
        beta,
        tau_time,   # in hours
        rho,
        gamma,
        building_source_types,
        building_destination_types,
        bounding_box,
        commuter_speed=1.0,
        model_crs="epsg:3857",
        show_walkway=False,
    ) -> None:
        super().__init__()
        self.schedule = mesa.time.RandomActivation(self)
        self.show_walkway = show_walkway
        self.data_crs = data_crs
        self.space = Campus(crs=model_crs)
        self.num_commuters = num_commuters
        self.building_source_types = building_source_types
        self.building_destination_types = building_destination_types
        self.bounding_box = bounding_box
        self.step_duration = step_duration
        Commuter.SPEED = commuter_speed * 60.0 * step_duration # meters per tick (5 minutes)
        Commuter.ALPHA = alpha
        Commuter.TAU_jump = tau_jump * 100
        Commuter.BETA = beta
        Commuter.TAU_time = tau_time * 60.0
        Commuter.RHO = rho
        Commuter.GAMMA = gamma
        self._load_buildings_from_file(buildings_file, crs=model_crs, region=region)
        self._load_road_vertices_from_file(walkway_file, crs=model_crs, region=region)
        self._set_building_entrance()
        self.got_to_destination = 0
        self.day = 0
        self.hour = 0
        self.minute = 0
        self._create_commuters()
        
        

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "time": get_time,
                "status_home": partial(get_num_commuters_by_status, status="home"),
                "status_work": partial(get_num_commuters_by_status, status="work"),
                "state_explore": partial(get_num_commuters_by_state, state="explore"),
                "state_return": partial(get_num_commuters_by_state, state="return"),
                "status_traveling": partial(
                    get_num_commuters_by_status, status="transport"
                ),
                "average_visited_locations": partial(
                    get_average_visited_locations
                ),
                "visited_locations": partial(
                    get_visited_locations
                ),
            }
        )
        self.datacollector.collect(self)

    def _create_commuters(self) -> None:
        for _ in range(self.num_commuters):
            random_home = self.space.get_random_home()
            commuter = Commuter(
                unique_id=uuid.uuid4().int,
                model=self,
                geometry=Point(random_home.centroid),
                crs=self.space.crs,
            )
            commuter.set_home(random_home)
            #commuter.set_work(random_work)
            #commuter.set_next_location(random_work)
            random_home.visited = True
            #random_work.visited = True 
            commuter.set_visited_location(random_home,1)
            commuter.S = 1
            commuter.status = "home"
            commuter.state = "explore"
            self.space.add_commuter(commuter)
            self.schedule.add(commuter)

    def _load_buildings_from_file(
        self, buildings_file: str, crs: str, region: str
    ) -> None:
        # Apply bounding box, later might be better to implement polygon filter that user can select from map
        buildings_df = gpd.read_file(buildings_file, bbox=(self.bounding_box))
        # Filter for source (home) and destination (work) buildings
        buildings_df = buildings_df[buildings_df['type'].isin(self.building_source_types+self.building_destination_types)] 
        buildings_type = [2 if x in self.building_source_types else 1 for x in buildings_df['type']]
        buildings_df.index.name = "unique_id"
        buildings_df = buildings_df.set_crs(self.data_crs, allow_override=True).to_crs(
            crs
        )
        buildings_df["centroid"] = [
            (x, y) for x, y in zip(buildings_df.centroid.x, buildings_df.centroid.y)
        ]
        building_creator = mg.AgentCreator(Building, model=self)
        buildings = building_creator.from_GeoDataFrame(buildings_df)
        self.space.add_buildings(buildings,buildings_type)

    def _load_road_vertices_from_file(
        self, walkway_file: str, crs: str, region: str
    ) -> None:
        walkway_df = (
            gpd.read_file(walkway_file, self.bounding_box)
            .set_crs(self.data_crs, allow_override=True)
            .to_crs(crs)
        )
        self.walkway = CampusWalkway(region=region, lines=walkway_df["geometry"])
        if self.show_walkway:
            walkway_creator = mg.AgentCreator(Walkway, model=self)
            walkway = walkway_creator.from_GeoDataFrame(walkway_df)
            self.space.add_agents(walkway)


    def _set_building_entrance(self) -> None:
        for building in (
            *self.space.homes,
            *self.space.works,
            *self.space.other_buildings,
        ):
            building.entrance_pos = self.walkway.get_nearest_node(building.centroid)

    def step(self) -> None:
        self.__update_clock()
        self.schedule.step()
        self.datacollector.collect(self)


#
    def __update_clock(self) -> None:
        self.minute += self.step_duration
        if self.minute == 60:
            if self.hour == 23:
                self.hour = 0
                self.day += 1
            else:
                self.hour += 1
            self.minute = 0


        
               
                    