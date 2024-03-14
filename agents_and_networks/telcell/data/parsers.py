"""
This module contains parser functions that read raw data and parse them into
`Measurement` or `Track` objects.
"""

import csv
from datetime import datetime
from itertools import groupby
from pathlib import Path
from typing import List, Union

from telcell.auxilliary_models.rare_pair.coverage_model import CoverageData
from telcell.data.models import Measurement, Track, Point


def parse_measurements_csv(path: Union[str, Path]) -> List[Track]:
    """
    Parse a `measurements.csv` file into `Track`s. The following columns are
    expected to be present:

        - owner
        - device
        - cellinfo.wgs84.lat
        - cellinfo.wgs84.lon
        - timestamp

    Any additional columns are stored under the `extra` attribute of each
    resulting `Measurement` object.

    :param path: The path to the `measurements.csv` file that should be parsed
    :return: All `Track`s that were constructed from the data
    """
    tracks = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        # We assume the rows in the csv file are already sorted by:
        #   1. owner
        #   2. device
        #   3. timestamp
        # If this is not the case, we first have to call `sorted()` here.
        measurements_sorted = sorted(reader,
                                     key=lambda row: (row["owner"],
                                                      row["device"],
                                                      row["timestamp"]))

        for (owner, device), group \
                in groupby(measurements_sorted, key=lambda row: (row["owner"], row["device"])):
            # In practice, we might need to consult an external database to
            # retrieve the (lat, lon) coordinates. In this case, they have
            # already been included in the `measurements.csv` input file.
            measurements = [
                Measurement(
                    coords=Point(lat=float(row['cellinfo.wgs84.lat']),
                                 lon=float(row['cellinfo.wgs84.lon'])),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    # For now, we just store the entire `row` under `extra`,
                    # even though this leads to some duplicate data.
                    # TODO: Make separate (telecom) (specific) parser
                    extra={'mnc': '16',
                           #'mnc': row['cell'].split('-')[1],
                           'azimuth': row['cellinfo.azimuth_degrees'],
                           'antenna_id': row.get('cellinfo.antenna_id', None),
                           'zipcode': row.get('cellinfo.zipcode', None),
                           'city': row.get('cellinfo.city', None)}
                ) for row in group
            ]
            track = Track(owner, device, measurements)
            tracks.append(track)
    return tracks


def parse_coverage_data_csv(path: Union[str, Path]) -> List[CoverageData]:
    """
    """
    data = {}
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['id'], row['time_diff_s'], row['antenna_mnc'])
            measurement = Measurement(
                coords=Point(lat=float(row['antenna_lat']), lon=float(row['antenna_lon'])),
                timestamp=None,
                extra={'bandwidth': row['antenna_bandwidth'],
                       'height': row['antenna_height'],
                       'azimuth': row['antenna_azimuth'],
                       'mnc': row['antenna_mnc'],
                       'radio': row['antenna_radio']})
            if key not in data:
                data[key] = {
                    'location': Measurement(
                        coords=Point(
                            lat=float(row['lm_lat']),
                            lon=float(row['lm_lon'])
                        ),
                        timestamp=None,
                        extra={}),
                    'negative_antennas': [],
                    'time_diff_s': row['time_diff_s']}
            if row['type'] == 'positive':
                if data[key].get('positive_antenna'):
                    raise KeyError('Positive antenna should be unique')
                data[key]['positive_antenna'] = measurement
            else:
                data[key]['negative_antennas'].append(measurement)
    if any(len(d.get('negative_antennas')) > 500 for d in data.values()):
        raise KeyError('A maximum of 500 negative antennas per key are allowed')
    return [CoverageData(**measurement) for measurement in data.values()]
