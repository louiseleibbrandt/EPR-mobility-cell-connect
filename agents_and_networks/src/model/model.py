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
        len(commuter.visited_locations) for commuter in model.schedule.agents 
    ]
    return sum(commuters)/len(commuters)


class AgentsAndNetworks(mesa.Model):
    schedule: mesa.time.RandomActivation
    output_file: csv
    start_date: str
    current_id: int
    space: Netherlands
    walkway: NetherlandsWalkway
    bounding_box:list
    bounding_box_trip:list
    num_commuters: int
    step_duration: int
    allow_trips: bool
    only_same_day_trips: bool
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
    common_work: Building
    datacollector: mesa.DataCollector
    

    def __init__(
        self,
        data_crs: str,
        buildings_file: str,
        buildings_file_trip: str,
        walkway_file: str,
        walkway_file_trip: str,
        num_commuters,
        step_duration,
        allow_trips,
        only_same_day_trips,
        alpha,
        tau_jump,   # in meters
        beta,
        tau_time,   # in hours
        rho,
        gamma,
        bounding_box,
        bounding_box_trip,
        commuter_speed,
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
        self.bounding_box = bounding_box
        self.bounding_box_trip = bounding_box_trip
        self.step_duration = step_duration
        self.allow_trips = allow_trips
        self.only_same_day_trips = only_same_day_trips
        self.positions_to_write = []
        self.positions = []

        Commuter.SPEED = commuter_speed * step_duration  # meters per tick 
        print("speed: ", Commuter.SPEED)
        Commuter.ALPHA = alpha
        Commuter.TAU_jump = tau_jump
        Commuter.BETA = beta
        Commuter.TAU_time = tau_time
        Commuter.RHO = rho
        Commuter.GAMMA = gamma

        Commuter.allow_trips = allow_trips
        Commuter.only_same_day_trips = only_same_day_trips


        self._load_buildings_from_file(buildings_file, buildings_file_trip, crs=model_crs)
        self._load_road_vertices_from_file(walkway_file, walkway_file_trip, crs=model_crs)
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
        date = self.start_date
        for i in range(self.num_commuters):
            random_home = self.space.get_random_building()
            commuter = Commuter(
                unique_id=uuid.uuid4().int,
                model=self,
                geometry=Point(random_home.centroid),
                crs=self.space.crs,
            )
            commuter.set_home(random_home)
            commuter.set_next_location(commuter.my_home)
            random_home.visited = True
            commuter.set_visited_location(random_home,5)
            commuter.status = "home"
            self.space.add_commuter(commuter, True)
            self.schedule.add(commuter)
            self.positions.append([commuter.geometry.x,commuter.geometry.y])
            self.positions_to_write.append([i,commuter.geometry.x,commuter.geometry.y,date,commuter.status])

    def _load_buildings_from_file(
        self, buildings_file: str, buildings_file_trip: str, crs: str
    ) -> None:
        # read in buildings from normal bounding box
        buildings_df = gpd.read_file(buildings_file, bbox=(self.bounding_box))
        buildings_df = buildings_df.sample(frac =  0.05)
        print("number buildings: ",len(buildings_df))
        # if allow trips, read in buildings from bounding box corresponding to trip
        if (self.allow_trips == True):
            buildings_df_trip = gpd.read_file(buildings_file_trip, bbox=(self.bounding_box_trip))
            buildings_df_trip = buildings_df_trip.sample(frac =  0.05)
            print("number buildings trip: ",len(buildings_df_trip))
            buildings_type = [0]*len(buildings_df) + [1]*len(buildings_df_trip)
            buildings_df = pd.concat([buildings_df,buildings_df_trip])
        else:
            buildings_type = [0]*len(buildings_df)


        buildings_df.index.name = "unique_id"
        buildings_df = buildings_df.set_crs(self.data_crs, allow_override=True).to_crs(
            crs
        )
        buildings_df["centroid"] = [
            (x, y) for x, y in zip(buildings_df.centroid.x, buildings_df.centroid.y)
        ]
        
        building_creator = mg.AgentCreator(Building, model=self)
        buildings = building_creator.from_GeoDataFrame(buildings_df)
        print(len(buildings))

        self.space.add_buildings(buildings,buildings_type)

    def _load_road_vertices_from_file(
        self, walkway_file: str, walkway_file_trip: str, crs: str
    ) -> None:
        if (self.allow_trips == True):
                                 
            # read in all roads for two cities
            files = [walkway_file,walkway_file_trip]
            boxes = [self.bounding_box,self.bounding_box_trip]
            walkway_df = gpd.GeoDataFrame(pd.concat([gpd.read_file(i,j) for (i,j) in zip(files,boxes)], 
                        ignore_index=True)).set_crs(self.data_crs, allow_override=True).to_crs(crs)
            
            # only read in motorways between cities
            bounding_box_full = (min(self.bounding_box[0],self.bounding_box_trip[0]),min(self.bounding_box[1],self.bounding_box_trip[1]),
                             max(self.bounding_box[2],self.bounding_box_trip[2]),max(self.bounding_box[3],self.bounding_box_trip[3])) 
            motorway_df = gpd.GeoDataFrame(pd.concat([gpd.read_file(i,bounding_box_full) for i in files], 
                        ignore_index=True)).set_crs(self.data_crs, allow_override=True).to_crs(crs)
            motorway_df = motorway_df[motorway_df['fclass'].isin(['motorway','motorway_link','secondary'])]

            # combine
            walkway_df = gpd.GeoDataFrame(pd.concat([walkway_df,motorway_df]))
        else:
            walkway_df = (
                gpd.read_file(walkway_file, self.bounding_box)
                .set_crs(self.data_crs, allow_override=True)
                .to_crs(crs)
            )
        self.walkway = NetherlandsWalkway(lines=walkway_df["geometry"])


    def _set_building_entrance(self) -> None:
        for building in (
            *self.space.buildings,
            *self.space.buildings_trip,
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
        
                
        
               
                    