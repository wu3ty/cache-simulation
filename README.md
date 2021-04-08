# cache-simulation - HTTP response cache simulation

Python script to simulate a HTTP response cache

## Introduction

Caching can help many applications to significantly reduce the response time. However, its benefit highly depends on the request patterns and configuration of a cache. _cache-simulator_ helps assessing the impact early on before implementing a real solution.

## Configuration

The following _hyperparameters_ of a cache can be configured:

* Time-To-Live (TTL): How long does an item stay in the cache before it is removed in seconds.
* Cache size: How many items can be stored in a cache
* Expiration Strategy S: Which item should be removed from the cache if it reached its capacity

## Data

To run a simulation, requests need to be provisioned in a CSV file, as in _debug.csv_. The input data needs to be available in the following format:

ID | timestamp | query
--- | --- | --- | ---
0 | 2021-03-22T00:00:01.085Z | http://.../parameter1=1
1 | 2021-03-22T00:00:02.085Z | hhttp://.../parameter1=2
2 | 2021-03-22T00:00:02.185Z | http://.../parameter1=1

ID is a unique ID of the request, timestamp the real-time timestamp in the format _"%Y-%m-%dT%H:%M:%S.%fZ_ and the query represents the individual request.

## Simulation Logic without Response Knowledge

For a start, we assume do not have the JSON response available. Thus, the only _simulation_ we can perform is to understand the amount of cache hits based on request patterns. The following flow chart shows on a high-level how the simulation is implemented.

::: mermaid
graph LR;
    A[Requests]-->B[Cache expiration];
    subgraph sg1 [Cache Simulation]
    B-->C{Request cached};
    C--yes-->D[Hit];
    C--no-->E[Simulate request];
    E-->F{Cache size exeeded};
    F--yes-->G[Displace item];
    F--no-->H[Cache request];
    G-->H;
    end
:::

All requests in an input CSV file are individually executed through the simulator, thus giving the simulation the current time based on the request's _timestamp_. Then, the application first expires all elements in the cache that are older than timestamp - TTL. Then, if the request is still cached, it is counted as a hit. Otherwise, a calculation or on-premise request needs to be performed (here, it is just a blank action counting the miss), and the cache size evaluated. If the cache is already at capacity, one item will be removed based on the expiration strategy. We use a commonly applied least recently used (LRU) displacement strategy here. At the end, the request is cached and the application proceeds with the next request.

## Prerequisites

* Python 3 (tested with 3.6.3)
* Python packages: pip3 install requirements.txt

## Running the application

* Try it: _make run_ in console
* Run in terminal/ console: _python3 cache_sim.py --help_
* Running unit tests: _make test_
