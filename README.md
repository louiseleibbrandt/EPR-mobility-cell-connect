Agents and Networks Model
=========================

![Delft Example](agents_and_networks/outputs/figures/epr_example.png)



## Summary

This is an implementation is based on the [GMU-Social Model](https://github.com/abmgis/abmgis/blob/master/Chapter08-Networks/Models/GMU-Social/README.md) in Python, using [Mesa](https://github.com/projectmesa/mesa) and [Mesa-Geo](https://github.com/projectmesa/mesa-geo).

In this model, EPR is run. All parameters can be chosen through the user interface and correspond to the truncated power law distributions modelling jump length and  waiting time in the CTRW. The exploration and preferential return probabilies can also be specified. Agents' commute routes can be found as the shortest path between entrances of their home and desired destination. These commute routes are segmented according to agents' walking speed. In this way, the movements of agents are constrained on the road network.

### GeoSpace

The GeoSpace contains multiple vector layers, including buildings, and a road network. More specifically, the road network is constructed from the polyline data and implemented by two underlying data structures: a topological network and a k-d tree. First, by treating road vertices as nodes and line segments as links, a topological network is created using the NetworkX and momepy libraries. NetworkX also provides several methods for shortest path computations (e.g., Dijkstra, A-star). Second, a k-d tree is built for all road vertices through the Scikit-learn library for the purpose of nearest vertex searches.

### GeoAgent

The commuters are the GeoAgents.

## How to run

First install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then run the trajectory model:

```bash
python3 scripts/run.py 
```

Then run the cell-tower sampling model (make sure you adjust the input parameters for desired sampling):
With coverage model:
```bash
python3 scripts/run_cell/coverage.py 
```

With simple sampling (closest cell tower facing agent):
```bash
python3 scripts/run_cell/simple.py 
```

Change `zuid-holland` to ... for a different region.

Open your browser to [http://127.0.0.1:8521/](http://127.0.0.1:8521/) and press `Start`.

## License

The data is from the [GMU-Social Model](https://github.com/abmgis/abmgis/blob/master/Chapter08-Networks/Models/GMU-Social/README.md) and is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).
