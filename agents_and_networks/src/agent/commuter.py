from __future__ import annotations
import math

import random
import sys
import uuid

import mesa
import mesa_geo as mg
import numpy as np
import pyproj
import geopandas as gpd
from shapely.geometry import LineString, Point
from src.agent.building import Building
from src.agent.geo_agents import Path
from src.space.utils import UnitTransformer, redistribute_vertices, power_law_exponential_cutoff


class Commuter(mg.GeoAgent):
    unique_id: int  # commuter_id, used to link commuters and nodes
    model: mesa.Model
    geometry: Point
    crs: pyproj.CRS
    origin: Building  # where he begins his trip
    destination: Building  # the destination he wants to arrive at
    my_path: list[
        mesa.space.FloatCoordinate
    ]  # a set containing nodes to visit in the shortest path
    step_in_path: int  # the number of step taking in the walk
    my_home: Building
    my_work: Building
    next_location: Building
    visited_locations: list[
        Building
    ]
    frequencies: list[int]
    S: float
    wait_time_h: int  # time to start going to work, hour and minute
    wait_time_m: int
    status: str  # work, home, or transport
    SPEED: float
    ALPHA: float # jump
    TAU_jump: float # max jump
    BETA: float # time
    TAU_time: float # max time
    RHO: float 
    GAMMA: float




    def __init__(self, unique_id, model, geometry, crs) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.S = 0.0
        self.my_home = None
        self.visited_locations = []
        self.frequencies = []
        self._set_wait_time()
        

    def __repr__(self) -> str:
        return (
            f"Commuter(unique_id={self.unique_id}, geometry={self.geometry}, "
        )

    def _set_wait_time(self) -> None:
        # Total time passed in minutes
        time_passed_m = (self.model.hour * 60) + self.model.minute
        # Get waiting time 
        wait_time_m = (power_law_exponential_cutoff(1, self.TAU_time, self.BETA, self.TAU_time))*60
        # Set correct new time
        total_time_m = wait_time_m + time_passed_m
        self.wait_time_h = math.floor(total_time_m/60)
        self.wait_time_m = int((total_time_m-self.wait_time_h*60))
         
        # Hour resets ever 24 hours
        if (self.wait_time_h >= 24):
            self.wait_time_h = self.wait_time_h % 24

            
        

    def set_home(self, new_home: Building) -> None:
        old_home_pos = self.my_home.centroid if self.my_home else None
        self.my_home = new_home
        self.model.space.update_home_counter(
            old_home_pos=old_home_pos, new_home_pos=self.my_home.centroid
        )

    def set_work(self, new_work: Building) -> None:
        self.my_work = new_work
    
    def set_next_location(self, next_location: Building) -> None:
        self.next_location = next_location
    
    def set_visited_location(self, location: Building, frequency: int) -> None:
        self.visited_locations.append(location)
        self.frequencies.append(frequency)

    def step(self) -> None:
        self._prepare_to_move()
        self._move()



    def _prepare_to_move(self) -> None:
        if (
            (self.status == "home" or self.status == "work" or self.status == "other")
            and (self.model.hour == self.wait_time_h and self.model.minute >= self.wait_time_m)
        ):
            self.origin = self.next_location
            # self.model.space.move_commuter(self, pos=self.geometry, update_idx = True)
            p = self.RHO*(math.pow(self.S,(-1*self.GAMMA)))

            if random.uniform(0, 1) < p:
                self._explore()
            else:
                self._return()
            
            self.destination = self.model.space.get_building_by_id(
                self.next_location.unique_id
            )
            self._path_select()
            self.status = "transport"
            

    def _move(self) -> None:
        if self.status == "transport":
            if self.step_in_path < len(self.my_path):
                next_position = self.my_path[self.step_in_path]
                self.model.space.move_commuter(self, next_position, False)
                self.step_in_path += 1
            else:
                self.model.space.move_commuter(self, self.destination.centroid,True)
                self._set_wait_time()
                if self.destination == self.my_home:
                    print("HOME!")
                    self.status = "home"
                else:
                    self.status = "other"
                


    def _explore(self) -> None:
        # Draw jump length from power distribution
        # jump_length = (power_law_exponential_cutoff(1, self.TAU_jump, self.ALPHA, self.TAU_jump)*100)
        # length = 1000000
        # min_length = 1000000
        # max_search = 0

        # # Search for new location with travelling distance similar to jump length (allowing 20% extra length)
        # # Runs for max 10 iterations, if no location found, pick location with min traveling distance
        # while(length >= jump_length+(jump_length*0.2) + 200 and max_search < 5):
        #     # Calculate new point based on random angle starting at current position
        #     theta = random.uniform(0, 2*math.pi)
        #     new_point = Point(self.geometry.x + jump_length * math.cos(theta),
        #         self.geometry.y + jump_length * math.sin(theta))
        #     new_location = self.model.space.get_nearest_building(new_point)

        #     # Calculate length to new location
        #     length = self.model.walkway.get_length_shortest_path(source=self.origin.entrance_pos, target=new_location.entrance_pos)
            
        #     # Update min parameters
        #     if (length < min_length): min_length, min_location = length, new_location
        #     max_search += 1
        jump_length = (power_law_exponential_cutoff(1, self.TAU_jump, self.ALPHA, self.TAU_jump)*100)
        theta = random.uniform(0, 2*math.pi)
        new_point = Point(self.geometry.x + jump_length * math.cos(theta),
        self.geometry.y + jump_length * math.sin(theta))
        min_location = self.model.space.get_nearest_building(new_point)

        # Set new location as building closest to this point
        min_location.visited = True
        self.set_next_location(min_location)

        # Update parameters 
        self.S = self.S + 1
        self.visited_locations.append(min_location)
        self.frequencies.append(1)
        

    def _return(self) -> None:
        while (new_location := random.sample(population=self.visited_locations,k=1,counts=self.frequencies))[0] == self.next_location:
             continue
        # new_location = random.sample(population=self.visited_locations,k=1,counts=self.frequencies)
        index = self.visited_locations.index(new_location[0])
        self.frequencies[index] += 1
        self.set_next_location(new_location[0])




    def _path_select(self) -> None:
        self.step_in_path = 0
        if (
            cached_path := self.model.walkway.get_cached_path(
                source=self.origin.entrance_pos, target=self.destination.entrance_pos
            )
        ) is not None:
            self.my_path = cached_path
        else:
            self.my_path = self.model.walkway.get_shortest_path(
                source=self.origin.entrance_pos, target=self.destination.entrance_pos
            )
            self.model.walkway.cache_path(
                source=self.origin.entrance_pos,
                target=self.destination.entrance_pos,
                path=self.my_path,
            )
            
        self._redistribute_path_vertices()


    def _redistribute_path_vertices(self) -> None:
        # if origin and destination share the same entrance, then self.my_path
        # will contain only this entrance node,
        # and len(self.path) == 1. There is no need to redistribute path vertices.
        if len(self.my_path) > 1:
            unit_transformer = UnitTransformer(degree_crs=self.model.walkway.crs)
            original_path = LineString([Point(p) for p in self.my_path])
            # from degree unit to meter
            path_in_meters = unit_transformer.degree2meter(original_path)

            redistributed_path_in_meters = redistribute_vertices(
                path_in_meters, self.SPEED
            )
            # meter back to degree
            redistributed_path_in_degree = unit_transformer.meter2degree(
                redistributed_path_in_meters
            )
            self.my_path = list(redistributed_path_in_degree.coords)

