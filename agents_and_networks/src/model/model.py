import uuid
from functools import partial
import geopandas as gpd
import numpy as np
import mesa
import mesa_geo as mg
import pandas as pd
from shapely.geometry import Point
import csv

from datetime import datetime, timedelta

from src.agent.building import Building
from src.agent.commuter import Commuter
from src.space.netherlands import Netherlands
from src.space.road_network import NetherlandsWalkway
from shapely.geometry import Point
from scipy.stats import poisson

from pyproj import Transformer


def get_time(model) -> pd.Timedelta:
    return pd.Timedelta(days=model.day, hours=model.hour, minutes=model.minute)


def get_num_commuters_by_status(model, status: str) -> int:
    commuters = [
        commuter for commuter in model.schedule.agents if commuter.status == status
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
    start_date: str
    current_id: int
    space: Netherlands
    walkway: NetherlandsWalkway
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
        start_date="2023-05-01",
    ) -> None:
        super().__init__()
        self.schedule = mesa.time.RandomActivation(self)
        self.start_date = datetime.strptime(start_date,"%Y-%m-%d")
        self.data_crs = data_crs
        self.space = Netherlands(crs=model_crs)
        self.num_commuters = num_commuters
        self.space.number_commuters = num_commuters
        self.building_source_types = building_source_types
        self.building_destination_types = building_destination_types
        self.bounding_box = bounding_box
        self.step_duration = step_duration
        self.positions_to_write = []
        self.positions = []

        Commuter.SPEED = commuter_speed * step_duration  # meters per tick (5 seconds)
        Commuter.ALPHA = alpha
        Commuter.TAU_jump = tau_jump
        Commuter.BETA = beta
        Commuter.TAU_time = tau_time
        Commuter.RHO = rho
        Commuter.GAMMA = gamma

        self._load_buildings_from_file(buildings_file, crs=model_crs)
        self._load_road_vertices_from_file(walkway_file, crs=model_crs)


        self._set_building_entrance()

        self.day = 0
        self.hour = 0
        self.minute = 0
        self.second = 0
        
        self.writing_id_trajectory = 0
        self._create_commuters() 
        output_file_trajectory = open(f'././outputs/trajectories/output_trajectory.csv', 'w')
        csv.writer(output_file_trajectory).writerow(['id','owner','timestamp','cellinfo.wgs84.lon','cellinfo.wgs84.lat','status'])    

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "time": get_time,
                "status_home": partial(get_num_commuters_by_status, status="home"),
                "status_work": partial(get_num_commuters_by_status, status="work"),
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
        # date = datetime(2023, 5, self.day+1, self.hour, self.minute, self.second, 0)
        date = self.start_date
        for i in range(self.num_commuters):
            random_home = self.space.get_random_home()
            random_work = self.space.get_random_work()
            commuter = Commuter(
                unique_id=uuid.uuid4().int,
                model=self,
                geometry=Point(random_home.centroid),
                crs=self.space.crs,
            )
            commuter.set_home(random_home)
            commuter.set_work(random_work)
            commuter.set_next_location(commuter.my_home)
            random_home.visited = True
            commuter.set_visited_location(random_home,50)
            commuter.set_visited_location(random_work,50)
            commuter.S = 1
            commuter.status = "home"
            self.space.add_commuter(commuter, True)
            self.schedule.add(commuter)
            self.positions.append([commuter.geometry.x,commuter.geometry.y])
            self.positions_to_write.append([i,commuter.geometry.x,commuter.geometry.y,date])

    def _load_buildings_from_file(
        self, buildings_file: str, crs: str
    ) -> None:
        buildings_df = gpd.read_file(buildings_file, bbox=(self.bounding_box))
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
        self, walkway_file: str, crs: str
    ) -> None:
        walkway_df = (
            gpd.read_file(walkway_file, self.bounding_box)
            .set_crs(self.data_crs, allow_override=True)
            .to_crs(crs)
        )
        self.walkway = NetherlandsWalkway(lines=walkway_df["geometry"])


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

        total_seconds = self.day*24*60*60 + self.hour*60*60 + self.minute*60 + self.second
        time = self.start_date + timedelta(seconds = total_seconds)

        for i in range(self.num_commuters):
            commuter = self.schedule.agents[i]
            x = commuter.geometry.x
            y = commuter.geometry.y
            if (self.positions[i][0] != x or self.positions[i][1] != y):
                self.positions_to_write.append([i,x,y,time,commuter.status])
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
                                   lat,lon,pos[4]])
            self.writing_id_trajectory += 1
        output_file.close()
        total_seconds = self.day*24*60*60 + self.hour*60*60 + self.minute*60 + self.second
        time = self.start_date + timedelta(seconds = total_seconds)
        print("time: ",time)
        print("average locations: ",get_average_visited_locations(self))
        


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
        
                
        
               
                    