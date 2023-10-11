import profile
import uuid
from functools import partial
import geopandas as gpd
import numpy as np
import mesa
import mesa_geo as mg
import pandas as pd
from shapely.geometry import Point
import csv
import math
from datetime import datetime

from src.agent.building import Building
from src.agent.commuter import Commuter
from src.agent.geo_agents import Walkway
from src.space.campus import Campus
from src.space.road_network import CampusWalkway
from shapely.geometry import Point
from src.space.utils import power_law_exponential_cutoff

from pyproj import Transformer


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

def get_average_visited_locations(model) -> list:
    commuters = [
        commuter.S for commuter in model.schedule.agents 
    ]
    return sum(commuters)/len(commuters)







class AgentsAndNetworks(mesa.Model):
    running: bool
    schedule: mesa.time.RandomActivation
    output_file: csv
    show_walkway: bool
    current_id: int
    space: Campus
    walkway: CampusWalkway
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
    second: int
    p_time1: list[int]
    p_time2: list[int]
    writing_id: int
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
        self.space.number_commuters = num_commuters
        self.building_source_types = building_source_types
        self.building_destination_types = building_destination_types
        self.bounding_box = bounding_box
        self.step_duration = step_duration

        Commuter.SPEED = commuter_speed * step_duration  # meters per tick (5 seconds)
        Commuter.ALPHA = alpha
        Commuter.TAU_jump = tau_jump
        Commuter.BETA = beta
        Commuter.TAU_time = tau_time
        Commuter.RHO = rho
        Commuter.GAMMA = gamma

        self._load_buildings_from_file(buildings_file, crs=model_crs, region=region)
        self._load_road_vertices_from_file(walkway_file, crs=model_crs, region=region)
        self._set_building_entrance()
        self.day = 0
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.writing_id = 0
        self._create_commuters() 
        self.p_time1 = np.random.exponential(3.45,self.num_commuters)*180
        self.p_time2 = np.random.exponential(3.45,self.num_commuters)*180

        # reset output file
        output_file = open('././outputs/trajectories/output.csv', 'w')
        csv.writer(output_file).writerow(['id','owner','device','timestamp','cellinfo.wgs84.lon','cellinfo.wgs84.lat','cellinfo.azimuth_degrees','cell'])    
              

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
            commuter.set_next_location(commuter.my_home)
            random_home.visited = True
            commuter.set_visited_location(random_home,1)
            commuter.S = 1
            commuter.status = "home"
            commuter.state = "explore"
            self.space.add_commuter(commuter, True)
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
        

        time_passed_seconds = self.hour*60*60 + self.minute*60 + self.second
        

        for i in range(self.num_commuters):
            # should reset ever 24 hours (24*60)
            if (time_passed_seconds <= self.step_duration):
                self.p_time1[i] = np.random.exponential(3.45,1)*180
                self.p_time2[i] = np.random.exponential(3.45,1)*180

            if (time_passed_seconds >= self.p_time1[i]):
                self.p_time1[i] = time_passed_seconds+ np.random.exponential(3.45,1)*180
                self.__write_to_file(i, 1)
            if (time_passed_seconds >= self.p_time2[i]):
                self.p_time2[i] = time_passed_seconds + np.random.exponential(3.45,1)*180
                self.__write_to_file(i, 2)
        self.datacollector.collect(self)
    

    def __write_to_file(self, agent: int, phone: int) -> None:
        output_file = open('././outputs/trajectories/output.csv', 'a')
        output_writer = csv.writer(output_file)

        commuter = self.schedule.agents[agent]
        x,y = Transformer.from_crs("EPSG:3857","EPSG:4326").transform(commuter.geometry.x,commuter.geometry.y)
        
        output_writer.writerow([self.writing_id, f"Agent{chr(agent + 65)}", f"{chr(agent + 65)}_{phone}", 
                                   datetime(2023, 5, self.day+1, self.hour, self.minute, self.second, 0),
                                   y,x,180,"0-0-0"])
        output_file.close()
        self.writing_id += 1


    def __update_clock(self) -> None:
        self.second += self.step_duration
        if self.second >= 60:
            while self.second/60 >= 1:
                self.minute += 1
                self.second -= 60
            if self.minute >= 60:
                while self.minute/60 >= 1:
                    self.hour += 1
                    self.minute -= 60
                if self.hour >= 23:
                    self.day += 1
                    self.hour = 0
        
                
        
               
                    