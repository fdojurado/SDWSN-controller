============================================================================================
Deploying a Wireless Sensor Network: A Step-by-Step Tutorial for Real-World Applications
============================================================================================

Wireless sensor networks have become an essential component of modern systems, enabling applications in various domains such as environmental monitoring, industrial automation, and smart cities. However, deploying a wireless sensor network in a real-world scenario can be challenging due to the complexity of the hardware, software, and networking components involved.

In this tutorial, we will guide you through the process of deploying a wireless sensor network step-by-step, starting from the hardware selection and installation to the network configuration and data visualization. We will use a popular open-source software package to facilitate the deployment process and provide you with a comprehensive understanding of the entire process.

Whether you are a researcher, engineer, or hobbyist, this tutorial will provide you with the knowledge and skills required to deploy a wireless sensor network in a real-world scenario successfully. So, let's get started!

Network topology
----------------

We will be deploying a small wireless sensor network consisting of two sensor nodes and a sink node. The sensor nodes will be equipped with sensors to collect data and communicate wirelessly with the sink node. The sink node will act as a gateway and will be directly connected to the controller via a serial interface. This setup will enable us to collect data from the sensor nodes and transmit it to the controller for analysis and processing.

We will assign NODE 2 and NODE 3 to the sensor nodes and NODE 3 to the sink node.

Hardware selection
------------------

Hardware Selection: Choose your wireless sensor platform that best suitable for your application. In this tutorial, we are using SensorTag_ from Texas Instruments.

Installation
------------

The sensor nodes run Contiki-NG-SDWSN_ in its core. To compile and flash the firmware, you need to install the required software packages, follow the instructions in the installation guide :ref:`here<Set up the data plane>`.

Setting up the network
----------------------

To set up the wireless sensor network, we will need to perform the following steps:

Compile and flash the firmware on the sensor nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To compile the firmware, follow the below steps.

#. Go to the directory where you have cloned the Contiki-NG-SDWSN_ repository::

    $ cd contiki-ng

#. To compile the firmware for the end nodes, navigate to the directory containing the code for the end nodes. In this case::

    $ cd examples/sdn-tsch-node

#. Compile the firmware for both sensor nodes::

    $ make TARGET=simplelink BOARD=sensortag/cc2650 NODEID=2 MAKE_WITH_SDN_ORCHESTRA=1
    $ make TARGET=simplelink BOARD=sensortag/cc2650 NODEID=3 MAKE_WITH_SDN_ORCHESTRA=1

#. To compile the firmware for the sink node, navigate to the directory containing the code for the sink. In this case::

    $ cd examples/sdn-tsch-sink

#. Compile the firmware for the sink node::

    $ make TARGET=simplelink BOARD=sensortag/cc2650 NODEID=1 MAKE_WITH_SDN_ORCHESTRA=1

.. _SensorTag: https://www.ti.com/tool/TIDC-CC2650STK-SENSORTAG
.. _Contiki-NG-SDWSN: https://github.com/fdojurado/contiki-ng
