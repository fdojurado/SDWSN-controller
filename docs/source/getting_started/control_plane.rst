=============
Control plane
=============

The module or repository that manages the control plane of the ELISE framework is SDWSN-Controller_. This is the main controller of the :ref:`Data plane<data_plane>`.

The SDWSN-Controller_ features the main functionalities described below:

* Multiple controller types including a container controller for the Cooja network simulator (Only docker is supported) and a controller for FIT-IoT-LAB_ platforms.
* A Reinforcement learning module to manage the environment, reward processing, and etc.
* TSCH module for designing and building schedules.
* Routing module to manage routing paths of the data plane.
* Serial interface that handles the communication with the sink node of the data plane.
* Packet processing module that contains a packet dissector to pack and unpack packets from data plane.
* A network reconfiguration module that handles the configuration functions of the network.


.. _Contiki-NG-SDWSN: https://github.com/fdojurado/contiki-ng
.. _SDWSN-Controller: https://github.com/fdojurado/SDWSN-controller
.. _FIT-IoT-LAB: https://www.iot-lab.info/
