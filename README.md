<!-- <img src="https://github.com/SDWSN-controller/SDWSN-controller.github.io/blob/develop/images/logo/Contiki_logo_2RGB.png" alt="Logo" width="256"> -->

# ELISE: The SDN-based solution for the next generation of IoT networks

<!-- [![Github Actions](https://github.com/SDWSN-controller/SDWSN-controller/workflows/CI/badge.svg?branch=develop)](https://github.com/SDWSN-controller/SDWSN-controller/actions)
[![Documentation Status](https://readthedocs.org/projects/SDWSN-controller/badge/?version=develop)](https://SDWSN-controller.readthedocs.io/en/develop/?badge=develop) -->
[![license](https://img.shields.io/badge/license-3--clause%20bsd-brightgreen.svg)](https://github.com/fdojurado/SDWSN-controller/blob/develop/LICENSE.md)
[![Latest release](https://img.shields.io/github/release/SDWSN-controller/SDWSN-controller.svg)](https://github.com/fdojurado/SDWSN-controller/releases/latest)
[![GitHub Release Date](https://img.shields.io/github/release-date/SDWSN-controller/SDWSN-controller.svg)](https://github.com/fdojurado/SDWSN-controller/releases/latest)
[![Last commit](https://img.shields.io/github/last-commit/SDWSN-controller/SDWSN-controller.svg)](https://github.com/fdojurado/SDWSN-controller/commit/HEAD)

<!-- [![Stack Overflow Tag](https://img.shields.io/badge/Stack%20Overflow%20tag-Contiki--NG-blue?logo=stackoverflow)](https://stackoverflow.com/questions/tagged/SDWSN-controller) -->
<!-- [![Gitter](https://img.shields.io/badge/Gitter-Contiki--NG-blue?logo=gitter)](https://gitter.im/SDWSN-controller) -->
[![Twitter](https://img.shields.io/badge/Twitter-%40contiki__NG__SDWSN-blue?logo=twitter)](https://twitter.com/fdojurado)

ELISE is built upon multidisciplinary research efforts of Software-Defined Networking (SDN), Wireless Sensor Networks (WSNs), and Machine Learning (ML).

The ELISE project comprises two main componenets: [SDWSN Network OS](https://github.com/fdojurado/contiki-ng) and the SDWSN controller.

## SDWSN Controller

The SDWSN controller features the main functionalities described below:

* Multiple controller types including a container controller for the Cooja network simulator (Only docker is supported) and a controller for FIT IoT LAB platforms.
* A Reinforcement learning module to manage the environment, reward processing, and etc.
* A mongo database that stored network information.
* TSCH module for designing and building schedules.
* Routing module to manage routing paths of the SDWSN.
* Serial interface that handles the communication with the sink node of the SDWSN.
* Packet processing module that contains a packet dissector to pack and unpack packets from the SDWSN.
* A network reconfiguration module that handles the configuration functions of the network.

## SDWSN Network OS

The SDWSN protocol, also called "**Contiki-NG-SDWSN**", is the protocol that runs on the network infrastructure or constrained devices and on the edge controller. More info can be found at https://github.com/fdojurado/contiki-ng


This repository has all components added as submodules, and it also has scripts to automate experiments in the FIT IoT LAB platform. 

## Documentation

* GitHub repository: https://github.com/fdojurado/SDWSN-controller
* GitHub repository: https://github.com/fdojurado/contiki-ng
* Documentation: http://sdwsn-controller.readthedocs.io/
<!-- * Web site: http://contiki-ng.org -->
<!-- * Nightly testbed runs: https://contiki-ng.github.io/testbed -->

Engage with the community:

* Discussions on GitHub: https://github.com/fdojurado/SDWSN-controller/discussions
* Twitter: https://twitter.com/fdojurado

## License
[BSD 3-Clause License](https://github.com/fdojurado/SDWSN-controller/blob/main/LICENSE)
## Repository structure
