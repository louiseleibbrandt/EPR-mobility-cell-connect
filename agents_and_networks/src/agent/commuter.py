from __future__ import annotations

import random
import uuid

import mesa
import mesa_geo as mg
import numpy as np
import pyproj
from shapely.geometry import LineString, Point

from src.agent.building import Building
from src.agent.geo_agents import Path
from src.space.utils import UnitTransformer, redistribute_vertices


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
    start_time_h: int  # time to start going to work, hour and minute
    start_time_m: int
    end_time_h: int  # time to leave work, hour and minute
    end_time_m: int
    status: str  # work, home, or transport
    SPEED: float

    def __init__(self, unique_id, model, geometry, crs) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.my_home = None
        self.start_time_h = round(np.random.normal(6.5, 1))
        while self.start_time_h < 6 or self.start_time_h > 9:
            self.start_time_h = round(np.random.normal(6.5, 1))
        self.start_time_m = np.random.randint(0, 12) * 5
        self.end_time_h = self.start_time_h + 8  # will work for 8 hours
        self.end_time_m = self.start_time_m

    def __repr__(self) -> str:
        return (
            f"Commuter(unique_id={self.unique_id}, geometry={self.geometry}, "
        )

    def set_home(self, new_home: Building) -> None:
        old_home_pos = self.my_home.centroid if self.my_home else None
        self.my_home = new_home
        self.model.space.update_home_counter(
            old_home_pos=old_home_pos, new_home_pos=self.my_home.centroid
        )

    def set_work(self, new_work: Building) -> None:
        self.my_work = new_work

    def step(self) -> None:
        self._prepare_to_move()
        self._move()


    def _prepare_to_move(self) -> None:
        # start going to work
        if (
            self.status == "home"
            and self.model.hour == self.start_time_h
            and self.model.minute == self.start_time_m
        ):
            self.origin = self.model.space.get_building_by_id(self.my_home.unique_id)
            self.model.space.move_commuter(self, pos=self.origin.centroid)
            self.destination = self.model.space.get_building_by_id(
                self.my_work.unique_id
            )
            self._path_select()
            self.status = "transport"
        # start going home
        elif (
            self.status == "work"
            and self.model.hour == self.end_time_h
            and self.model.minute == self.end_time_m
        ):
            self.origin = self.model.space.get_building_by_id(self.my_work.unique_id)
            self.model.space.move_commuter(self, pos=self.origin.centroid)
            self.destination = self.model.space.get_building_by_id(
                self.my_home.unique_id
            )
            self._path_select()
            self.status = "transport"

    def _move(self) -> None:
        if self.status == "transport":
            if self.step_in_path < len(self.my_path):
                next_position = self.my_path[self.step_in_path]
                self.model.space.move_commuter(self, next_position)
                self.step_in_path += 1

            else:
                self.model.space.move_commuter(self, self.destination.centroid)
                if self.destination == self.my_work:
                    self.status = "work"
                elif self.destination == self.my_home:
                    self.status = "home"
                self.model.got_to_destination += 1

    def advance(self) -> None:
        raise NotImplementedError

    def _relocate_home(self) -> None:
        while (new_home := self.model.space.get_random_home()) == self.my_home:
            continue
        self.set_home(new_home)

    def _relocate_work(self) -> None:
        while (new_work := self.model.space.get_random_work()) == self.my_work:
            continue
        self.set_work(new_work)

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
            print(self.my_path)

