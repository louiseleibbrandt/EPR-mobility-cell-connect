from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from typing import Any, Mapping, Tuple, Sequence, Iterator, Union

import pyproj
from pyproj import Proj, Geod, Transformer

RD = ("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 "
      "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel "
      "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 "
      "+units=m +no_defs")
GOOGLE = ('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 '
          '+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m '
          '+nadgrids=@null +no_defs +over')
WGS84 = '+proj=latlong +datum=WGS84'
rd_projection = Proj(RD)
google_projection = Proj(GOOGLE)
wgs84_projection = Proj(WGS84)
geodesic = Geod('+ellps=sphere')
WGS84_TO_RD = Transformer.from_proj(wgs84_projection, rd_projection)
RD_TO_WGS84 = Transformer.from_proj(rd_projection, wgs84_projection)
# TODO: Realistic boundsx
rd_x_range = (1000, 350000)
rd_y_range = (1000, 700000)
GEOD_WGS84 = pyproj.Geod(ellps='WGS84')


def approximately_equal(first, second, tolerance=.0001):
    return abs(first - second) < tolerance


@dataclass(frozen=True)
class RDPoint:
    x: float
    y: float

    def __post_init__(self):
        if self.x < rd_x_range[0] or self.x > rd_x_range[1] or self.y < \
                rd_y_range[0] or self.y > rd_y_range[1]:
            raise ValueError(f'Invalid rijksdriehoek coordinates: ({self.x=}, {self.y=}); '
                             f'allowed range: x={rd_x_range}, y={rd_y_range}.')

    @property
    def xy(self) -> Tuple[float, float]:
        return self.x, self.y

    def convert_to_wgs84(self) -> Point:
        lon, lat = RD_TO_WGS84.transform(self.x, self.y)
        return Point(lat=lat, lon=lon)

    def distance(self, other: Union[RDPoint, Point]) -> float:
        other_rd = other.convert_to_rd() if isinstance(other, Point) else other
        return math.sqrt(math.pow(self.x - other_rd.x, 2) + math.pow(self.y - other_rd.y, 2))

    def approx_equal(self, other: Union[RDPoint, Point], tolerance_m: float = 1) -> bool:
        return self.distance(other) < tolerance_m

    def __repr__(self):
        return f'RDPoint(x={self.x}, y={self.y})'


@dataclass(frozen=True)
class Point:
    lat: float
    lon: float

    def __post_init__(self):
        if self.lat < -90 or self.lat > 90 or self.lon < -180 or self.lon > 180:
            raise ValueError(f'Invalid wgs84 coordinates: ({self.lat=}, {self.lon=}).')

    @property
    def latlon(self) -> Tuple[float, float]:
        return self.lat, self.lon

    def convert_to_rd(self) -> RDPoint:
        x, y = WGS84_TO_RD.transform(self.lon, self.lat)
        return RDPoint(x=x, y=y)

    def distance(self, other: Union[RDPoint, Point]) -> float:
        self_rd = self.convert_to_rd()
        other_rd = other.convert_to_rd() if isinstance(other, Point) else other
        return math.sqrt(math.pow(self_rd.x - other_rd.x, 2) + math.pow(self_rd.y - other_rd.y, 2))

    def approx_equal(self, other: Union[RDPoint, Point], tolerance_m: int = 1) -> bool:
        return self.distance(other) < tolerance_m

    def __eq__(self, other):
        if isinstance(other, Point):
            return (self.lat == other.lat) and (self.lon == other.lon)
        else:
            return False

    def __repr__(self):
        return f'Point(lat={self.lat}, lon={self.lon})'


@dataclass(eq=True, frozen=True)
class Measurement:
    """
    A single measurement of a device at a certain place and time.

    :param coords: The WGS84 latitude and longitude coordinates
    :param timestamp: The time of registration
    :param extra: Additional metadata related to the source that registered
            this measurement. These could for example inform the accuracy or
            uncertainty of the measured WGS84 coordinates.
    """
    coords: Point
    timestamp: datetime
    extra: Mapping[str, Any]

    @property
    def lat(self):
        return self.coords.lat

    @property
    def lon(self):
        return self.coords.lon

    @property
    def latlon(self):
        return self.coords.latlon

    @property
    def xy(self) -> Tuple[float, float]:
        return self.coords.convert_to_rd().xy

    def __str__(self):
        return f"<{self.timestamp}: ({self.lat}, {self.lon})>"

    def __hash__(self):
        return hash((self.lat, self.lon, self.timestamp.date(),
                     *(_extra for _extra in self.extra.values())))


@dataclass
class Track:
    """
    A history of measurements for a single device.

    :param owner: The owner of the device. Can be anything with a simcard.
    :param device: The name of the device.
    :param measurements: A series of measurements ordered by timestamp.
    """
    owner: str
    device: str
    measurements: Sequence[Measurement]

    def __len__(self) -> int:
        return len(self.measurements)

    def __iter__(self) -> Iterator[Measurement]:
        return iter(self.measurements)


@dataclass(order=False, frozen=True, eq=True)
class MeasurementPair:
    """
    A pair of two measurements. The pair can be made with different criteria,
    for example the time difference between the two measurements. It always
    contains the information from the two measurements it was created from.
    """

    measurement_a: Measurement
    measurement_b: Measurement

    @cached_property
    def time_difference(self):
        """Calculate the absolute time difference between the measurements."""
        return abs(self.measurement_a.timestamp - self.measurement_b.timestamp)

    @cached_property
    def distance(self):
        """Calculate the distance (in meters) between the two measurements of
        the pair."""
        _, _, distance = GEOD_WGS84.inv(self.measurement_a.lon,
                                        self.measurement_a.lat,
                                        self.measurement_b.lon,
                                        self.measurement_b.lat)
        return distance

    def __str__(self):
        return f"<{self.measurement_a}, ({self.measurement_b})>"
