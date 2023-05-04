=======================
Simple SDWSN controller
=======================

This tutorial sets up a simple controller that configures the routing paths and schedules of the data plane. In this case we use the Dijkstra algorithm for the routes and a contention free scheduler::

    from sdwsn-controller import *


Here, we use a controller for a data plane that run in a docker container.