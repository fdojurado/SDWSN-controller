# Experiment submission

This tutorial demonstrates how to submit an experiment in the FIT IoT LAB using python.

This experiment compiles the required firmwares in the current directory and deploys two sensors running the 'sdn-tsch-node' located at examples/sdn-tsch-node/ of the [**Contiki-NG-SDWSN**](https://github.com/fdojurado/contiki-ng) repository, and one sensor running 'sdn-tsch-sink' located at examples/sdn-tsch-sink/ of the same repository. It then reads from the serial interface data captured at the sink.

## Usage

main.py [-h] [-pt PLATFORM_TARGET] [-t TIME] [-s SITE] [-b BOARD] [-e END_NODE] [-c CONTROLLER] [-dbg DEBUG_LEVEL] [-hp HOME_PORT] [-p TARGET_PORT] username password node_list [node_list ...]

This submits a experiment to the FIT-IoT LAB.

positional arguments:
  username              Username
  password              Password
  node_list             Sensor nodes list, the first node is assigned to the sink

options:
  -h, --help            show this help message and exit
  -pt PLATFORM_TARGET, --platform-target PLATFORM_TARGET
                        Sensor platform to use
  -t TIME, --time TIME  Length in minutes of the experiment
  -s SITE, --site SITE  FIT IoT LAB site
  -b BOARD, --board BOARD
                        Sensor board name
  -e END_NODE, --end-node END_NODE
                        Path, within Contiki folder, to the end node example
  -c CONTROLLER, --controller CONTROLLER
                        Path, within Contiki folder, to sink example
  -dbg DEBUG_LEVEL, --debug_level DEBUG_LEVEL
                        Debug level, default NOTSET.
  -hp HOME_PORT, --home-port HOME_PORT
                        home port
  -p TARGET_PORT, --target-port TARGET_PORT
                        target port
