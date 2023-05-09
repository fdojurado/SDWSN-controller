.. _tutorial_deploying_a_wireless_sensor_network:

============================================================================================
Deploying a Wireless Sensor Network: A Step-by-Step Tutorial for Real-World Applications
============================================================================================

Wireless sensor networks have become an essential component of modern systems, enabling applications in various domains such as environmental monitoring, industrial automation, and smart cities. However, deploying a wireless sensor network in a real-world scenario can be challenging due to the complexity of the hardware, software, and networking components involved.

In this tutorial, we will guide you through the process of deploying a wireless sensor network step-by-step, starting from the hardware selection and installation to the network configuration and data visualization. We will use a popular open-source software package to facilitate the deployment process and provide you with a comprehensive understanding of the entire process.

Whether you are a researcher, engineer, or hobbyist, this tutorial will provide you with the knowledge and skills required to deploy a wireless sensor network in a real-world scenario successfully. So, let's get started!

Network topology
----------------

We will be deploying a small wireless sensor network consisting of two sensor nodes and a sink node. The sensor nodes will be equipped with sensors to collect data and communicate wirelessly with the sink node. The sink node will act as a gateway and will be directly connected to the controller via a serial interface. This setup will enable us to collect data from the sensor nodes and transmit it to the controller for analysis and processing.

We will assign NODE 2 and NODE 3 to the sensor nodes and NODE 1 to the sink node.

Hardware selection
------------------

Hardware Selection: Choose your wireless sensor platform that best suit your application. In this tutorial, we are using SensorTag_ from Texas Instruments.

Installation
------------

The sensor nodes run Contiki-NG-SDWSN_ in its core. To compile and flash the firmware, you need to install the required software packages, follow the instructions in the installation guide :ref:`here<Set up the data plane>`.

Setting up the network
----------------------

To set up the wireless sensor network, we will need to perform the following steps:

Firmware compilation
~~~~~~~~~~~~~~~~~~~~

To compile the firmware, follow the below steps. You can compile it natively on your machine or use a Docker container. If you are using Docker, you need to start it before proceeding with the next steps.

#. Go to the directory where you have cloned the Contiki-NG-SDWSN_ repository.

.. code-block:: console

    $ cd contiki-ng

#. To compile the firmware for the end nodes, navigate to the directory containing the code for the end nodes. In this case.

.. code-block:: console

    $ cd examples/sdn-tsch-node

#. You can Compile the firmware for both sensor nodes as follows.

.. code-block:: console

    $ make TARGET=simplelink BOARD=sensortag/cc2650 NODEID=2 MAKE_WITH_SDN_ORCHESTRA=1

    $ make TARGET=simplelink BOARD=sensortag/cc2650 NODEID=3 MAKE_WITH_SDN_ORCHESTRA=1

.. admonition:: Note
    :class: tip

    You may want to rename the elf files to `node2.elf` and `node3.elf` for nodes 2 and 3, respectively. The `elf` file can be found under the build folder after the compilation is done.


#. To compile the firmware for the sink node, navigate to the directory containing the code for the sink. In this case.

.. code-block:: console

    $ cd examples/sdn-tsch-sink

#. Compile the firmware for the sink node.

.. code-block:: console

    $ make TARGET=simplelink BOARD=sensortag/cc2650 NODEID=1 MAKE_WITH_SDN_ORCHESTRA=1

.. admonition:: Note
    :class: tip

    You may want to name the elf file to e.g. `node1.elf`.


Flash the firmware
~~~~~~~~~~~~~~~~~~

To flash the firmware, it is best to use the software tool recommended by the manufacturer of the wireless sensor platform. In this tutorial, we use the Uniflash_ tool from Texas Instruments.

#. Connect the wireless sensor platform to your computer via a USB cable.
#. Open the Uniflash tool.
#. Flash the firmware to the corresponding nodes.

Run the network
---------------

#. Connect the wireless sensor platform programmed with the sink firmware, in this case, `node1.elf`, to your computer via a USB cable.
#. Open a terminal and navigate to the directory where you have cloned the SDWSN-Controller_ repository, and activate the virtual environment.

    .. code-block:: console

        $ cd SDWSN-controller

        $ source venv/bin/activate

#. Navigate to the long-run tutorial directory.

    .. code-block:: console

        $ cd tutorials/reinforcement_learning/long_run

#. Prepare the configuration file (JSON) for the controller. In this case, we will use the below configuration.

    .. code-block:: json

        {
            "name": "example",
            "controller_type": "USB controller",
            "network": {
                "name": "Real WSN deployment",
                "processing_window": 20
            },
            "sink_comm": {
                "name": "serial",
                "host_dev": "/dev/tty.usbmodemL12371",
                "port_baud": 115200
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
            "reinforcement_learning": {
                "reward_processor": "EmulatedRewardProcessing",
                "max_episode_steps": 50000
            },
            "performance_metrics": {
                "energy": {
                    "weights": [
                        1.56292719e-08,
                        -2.99240537e-06,
                        2.12532630e-04,
                        -6.88468887e-03,
                        2.08470100e-01
                    ],
                    "norm_offset": 0.86
                },
                "delay": {
                    "weights": [
                        2.99098391e-08,
                        -6.28217483e-07,
                        6.09770278e-04,
                        4.66875245e-04
                    ],
                    "norm_offset": 0.94
                },
                "pdr": {
                    "weights": [
                        9.86763397e-18,
                        1.00000000e+00
                    ],
                    "norm_offset": 0.0
                }
            }
        }

#. Run the controller. Before running the controller, make sure that the sink node is connected to your computer via a USB cable, and that the `CONFIG_FILE` variable in the `simple_controller.py` is pointing to the configuration file you have prepared in the previous step.

    .. code-block:: console

        $ python3 long_run.py

.. admonition:: Note
    :class: tip

    Bear in mind that the collection of data from the sensor nodes may take some minutes. You can monitor the progress of the data collection in the terminal.

Visualization tool
------------------

You may want to connect a visualization tool to the controller to monitor the network. We have also developed a visualization tool that you can use to visualize the network. To use it, follow the below steps.

* Clone the SDWSN-GUI_ repository, and navigate to the directory.

    .. code-block:: console

        $ git clone https://github.com/fdojurado/SDWSN-GUI.git

        $ cd SDWSN-GUI

* Create a virtual environment and activate it.

    .. code-block:: console

        $ python3 -m venv venv

        $ source venv/bin/activate

* Install the visualization tool.

    .. code-block:: console

        $ pip install -e .

* Before running the visualization tool, we need to instruct the controller to establish the communication with the upper layer, in this case the visualization tool, this communication is establish through the MQTT protocol. In the configuration file you have prepared in the previous step add the below code block.

    .. code-block:: json

        "mqtt": {
            "host": "localhost",
            "port": 1883,
            "authentication": {
                "username": "foo",
                "password": "bar"
            }
        }

* As we are running the MQTT broker locally, we need to start it before running the visualization tool. Then, open a new terminal and start the MQTT broker.

* Run the visualization tool.

    .. code-block:: console

        $ cd examples/

        $ python3 sdwsn_gui.py




.. _SensorTag: https://www.ti.com/tool/TIDC-CC2650STK-SENSORTAG
.. _Contiki-NG-SDWSN: https://github.com/fdojurado/contiki-ng
.. _Uniflash: https://www.ti.com/tool/UNIFLASH
.. _SDWSN-Controller: https://github.com/fdojurado/SDWSN-controller
.. _SDWSN-GUI: https://github.com/fdojurado/SDWSN-GUI.git