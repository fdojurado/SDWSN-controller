=======================
Simple SDWSN controller
=======================

This tutorial sets up a simple controller that configures the routing paths and schedules of the data plane. In this case we use the Dijkstra algorithm for the routes and a contention free scheduler.

Configuration file
-------------------

Here, we need a configuration JSON file that specifies the modules that we want to use in the controller. For this example, we use the following configuration file.

.. code-block:: json

    {
        "name": "example",
        "controller_type": "native controller",
        "network": {
            "name": "Cooja",
            "processing_window": 200
        },
        "sink_comm": {
            "name": "socket",
            "host_dev": "127.0.0.1",
            "port_baud": 60001
        },
        "tsch": {
            "scheduler": "Contention Free Scheduler",
            "max_channel": 3,
            "max_slotframe": 70,
            "slot_duration": 10
        },
        "routing": {
            "algo": "Dijkstra"
        },
        "contiki": {
            "script_folder": "examples/elise",
            "source": "/Users/***/contiki-ng",
            "simulation_script": "cooja-orchestra.csc",
            "port": 60001
        }
    }

The configuration file is divided in different sections.

 * The first section is the name of the simulation, the type of controller to use.
 * The network section specifies the name of the network and the processing window. The processing window is the number of packets that the controller will process before sending the configuration to the data plane.
 * The next section is the sink communication. In this case, we use a socket communication. The host device is the IP address of the sink and the port baud is the port that the sink is listening to.
 * The next section is the TSCH configuration. Here, we specify the scheduler that we want to use, the maximum channel, the maximum slotframe and the slot duration.
 * Next, we specify the routing algorithm that we want to use.
 * The last section is the Contiki-NG-SDWSN_ configuration. Here, we specify the folder where the simulation files reside, the source folder of Contiki, the simulation script, and the port the sink is listening to.

Running the controller
----------------------

The python file for this example is ``simple_controller.py`` which is located in `tutorials/simple_controller/`.

To run the controller, we just need to execute the below command inside the example folder.

.. code-block:: console

    $ python simple_controller.py

The script starts the controller and Cooja. It then waits for the sink to connect. Once the sink is connected, the controller starts collecting network information. Next, it starts sending the configuration to the data plane. The controller stops once the cycle is finished.

.. _Contiki-NG-SDWSN: https://github.com/fdojurado/contiki-ng