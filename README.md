# Adaptive Signal Control

This repository contains a Python package (adasco) and several utility scripts (utils) for adaptive traffic signal control.

adasco can be used after adding it to your PYTHONPATH in one of two ways:
1. Install it using the install.sh and setup.py scripts (after creating a dummy test suite or excluding the test suite from the setup.py if required).
2. Manually add the fully qualified path of the adasco directory to your .bashrc.

## AdaSCo Architecture
AdaSCo uses the Simulation of Urban Mobility (SUMO) traffic simulator with custom schedulers and traffic signal control agents. Each adasco experiment runs a master process and several agent processes (one for each traffic intersection). The master process interfaces with SUMO, reads the simulation state (for example, detected vehicles on each road segment) at each time step, requests agents to compute traffic signal plans at decision steps and then controls the traffic lights in the SUMO simulation based on the agents' plans.
Agents compute plans using their custom planning methods and schedulers. Their plans are based on the current simulation state (traffic conditions, current traffic signal phase) provided by the master and also traffic information provided by other agents (neighbouring intersections). Agents thus interact with the master process and with other agents. Agent-Master communication occurs through messaging and Agent-Agent communication occurs through a data structure in shared memory.

Here is what the package looks like, followed by a brief description of each package component:

```
adasco
├── cluster.py
├── detector.py
├── master.py
├── messaging.py
├── preprocessor.py
├── registry.py
├── utils.py
├── schedulers
|   ├── cp.py
|   └── schic.py
└── agents
    ├── base.py
    ├── cp
    |   ├── saa.py
    |   ├── heuristic.py
    |   └── hindsight.py
    └── schic
        └── surtrac.py
```

- cluster.py: Contains utility methods for creating and manipulating vehicle clusters and vehicle cluster sequences.
- detector.py: Defines a traffic detector which reads vehicle data from a SUMO simulation.
- master.py: Defines the class for the master process which interfaces with SUMO and the traffic signal control agents.
- messaging.py: Defines message types for agent-master communication.
- preprocessor.py: Contains methods for preprocessing traffic data before planning. Also defines a class for sampling vehicle flows online (Sample), but this is not being used, if I remember correctly. Currently, we generate vehicle samples offline to ensure experiment repeatability.
- registry.py: Defines a list data structure (a registry) to help the master manage agents.
- utils.py: Contains common utility methods. I don't think this is being used by any of the scripts.
- schedulers: Contains implementations of our constraint-programming-based scheduler (cp.py) and the dynamic-programming-based scheduler used by SURTRAC (schic.py). 
- agents: Contains implementations of several agents which are all subclasses of the base agent (base.py). `agents/<scheduler>` contains agents based on a particular scheduler. All our main experiments use our sample average approximation agent (`adasco/cp/saa.py`) and SURTRAC (`adasco/schic/surtrac.py`).

## Utilities

The utils directory contains utility scripts for several tasks and many of these were created for one-off uses. I'd suggest reading the scripts carefully before using them. Most scripts use argparse for handling commandline argument so you should be able to use `python script.py -h` to learn about script usage. Here's a brief description of the different classes of scripts in this directory:

- results: Scripts for parsing log files and plotting results
- runners: Scripts for running experiments
- samples: Scripts for generating samples and reporting statistics about them
- scenarios: Scripts for generating test cases and traffic flows for experiments
- settings: Scripts for creating and tweaking parameter files for the experiment scenarios

Feel free to open an issue or get in touch if you have any questions or spot any issues!
