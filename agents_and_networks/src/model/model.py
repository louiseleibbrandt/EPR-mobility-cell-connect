import uuid
from functools import partial
import geopandas as gpd
import numpy as np
import mesa
import mesa_geo as mg
import pandas as pd
from shapely.geometry import Point
import csv

from datetime import datetime

from src.agent.building import Building
from src.agent.commuter import Commuter
from src.agent.geo_agents import Walkway
from src.space.campus import Campus
from src.space.road_network import CampusWalkway
from shapely.geometry import Point
from scipy.stats import poisson

from scripts.timer import Timer
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
    timer: Timer
    positions_to_write: list[int,float,float,datetime]
    positions: list[float,float]
    writing_id_trajectory:int
    datacollector: mesa.DataCollector
    

    def __init__(
        self,
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
        self.positions_to_write = []
        self.positions = []
        self.timer = Timer()

        Commuter.SPEED = commuter_speed * step_duration  # meters per tick (5 seconds)
        Commuter.ALPHA = alpha
        Commuter.TAU_jump = tau_jump
        Commuter.BETA = beta
        Commuter.TAU_time = tau_time
        Commuter.RHO = rho
        Commuter.GAMMA = gamma

        self._load_buildings_from_file(buildings_file, crs=model_crs)

        self.timer.start()
        self._load_road_vertices_from_file(walkway_file, crs=model_crs)
        print("walkway loaded")
        self.timer.stop()

        self._set_building_entrance()

        self.day = 0
        self.hour = 0
        self.minute = 0
        self.second = 0
        
        self.writing_id_trajectory = 0
        self._create_commuters() 
        output_file_trajectory = open(f'././outputs/trajectories/output_trajectory.csv', 'w')
        csv.writer(output_file_trajectory).writerow(['id','owner','timestamp','cellinfo.wgs84.lon','cellinfo.wgs84.lat'])    

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
        date = datetime(2023, 5, self.day+1, self.hour, self.minute, self.second, 0)
        for i in range(self.num_commuters):
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
            self.positions.append([commuter.geometry.x,commuter.geometry.y])
            self.positions_to_write.append([i,commuter.geometry.x,commuter.geometry.y,date])

    def _load_buildings_from_file(
        self, buildings_file: str, crs: str
    ) -> None:
        self.timer.start()
        bounding_box_rotterdam = (4.4306,51.9035,4.5092,51.9488)
        bounding_box_hague = (4.2617,52.0508,4.3571,52.1033)
        buildings_df = gpd.read_file(buildings_file, bbox=(self.bounding_box))
        # buildings_df = gpd.read_file(buildings_file, bbox=(bounding_box_rotterdam)).append(gpd.read_file(buildings_file, bbox=(bounding_box_hague)))
        print("buildings df read file1")
        self.timer.stop()
        self.timer.start()
        buildings_df = buildings_df[buildings_df['type'].isin(self.building_source_types+self.building_destination_types)] 
        print("buildings df read file2")
        self.timer.stop()
        self.timer.start()
        buildings_type = [2 if x in self.building_source_types else 1 for x in buildings_df['type']]
        print("buildings df type")
        self.timer.stop()
        self.timer.start()
        buildings_df.index.name = "unique_id"
        buildings_df = buildings_df.set_crs(self.data_crs, allow_override=True).to_crs(
            crs
        )
        print("buildings df crs")
        self.timer.stop()
        buildings_df["centroid"] = [
            (x, y) for x, y in zip(buildings_df.centroid.x, buildings_df.centroid.y)
        ]
        
        building_creator = mg.AgentCreator(Building, model=self)
        buildings = building_creator.from_GeoDataFrame(buildings_df)

        self.space.add_buildings(buildings,buildings_type)

    def _load_road_vertices_from_file(
        self, walkway_file: str, crs: str
    ) -> None:
        walkway_df = (
            gpd.read_file(walkway_file, self.bounding_box)
            .set_crs(self.data_crs, allow_override=True)
            .to_crs(crs)
        )
        self.walkway = CampusWalkway(lines=walkway_df["geometry"])
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

        self.timer.start()
        self.schedule.step()
        print("schedule step")
        self.timer.stop()

        time = datetime(2023, 5, self.day+1, self.hour, self.minute, self.second, 0)
        for i in range(self.num_commuters):
            commuter = self.schedule.agents[i]
            x = commuter.geometry.x
            y = commuter.geometry.y
            if (self.positions[i][0] != x or self.positions[i][1] != y):
                self.positions_to_write.append([i,x,y,time])
                self.positions[i][0] = x
                self.positions[i][1] = y


        if (self.minute == 0 & self.second==0):
            self.__write_to_file()
            self.positions_to_write = []
                
    
    def __write_to_file(self) -> None:
        output_file = open('././outputs/trajectories/output_trajectory.csv', 'a')
        output_writer = csv.writer(output_file)
        for pos in self.positions_to_write:
            lon,lat = Transformer.from_crs("EPSG:3857","EPSG:4326").transform(pos[1],pos[2])
            output_writer.writerow([self.writing_id_trajectory, f"Agent{pos[0]}", 
                                   pos[3],
                                   lat,lon])
            self.writing_id_trajectory += 1
        output_file.close()
        


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
                if self.hour >= 24:
                    self.day += 1
                    self.hour = 0
        
                
        
               
                    