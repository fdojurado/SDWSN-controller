#!/usr/bin/python3
#
# Copyright (C) 2022  Fernando Jurado-Lasso <ffjla@dtu.dk>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from sdwsn_controller.sink_communication.sink_comm import SinkComm
from sdwsn_controller.sink_communication.sink_serial import SinkSerial
from sdwsn_controller.reinforcement_learning.reward_processing \
    import EmulatedRewardProcessing
from sdwsn_controller.reinforcement_learning.numerical_reward_processing import NumericalRewardProcessing
from sdwsn_controller.config.performance_metrics import \
    PERFORMANCEMETRICSConfig
from sdwsn_controller.config.reinforcement_learning import REINFORCEMENTLEARNINGConfig


from sdwsn_controller.tsch.contention_free_scheduler import ContentionFreeScheduler
from sdwsn_controller.tsch.hard_coded_schedule import HardCodedScheduler

from sdwsn_controller.routing.dijkstra import Dijkstra


from sdwsn_controller.exceptions import ConfigurationFileNotFoundError
from sdwsn_controller.config.sink_comm import SINKCOMMConfig
from sdwsn_controller.config.network import NETWORKConfig
from sdwsn_controller.config.routing import ROUTINGConfig
from sdwsn_controller.config.contiki import CONTIKIConfig
from sdwsn_controller.config.docker import DOCKERConfig
from sdwsn_controller.config.tsch import TSCHConfig
from sdwsn_controller.config.mqtt import MQTTConfig
import json
import os
from pathlib import Path

REWARD_PROCESSORS = {
    'EmulatedRewardProcessing': EmulatedRewardProcessing,
    "NumericalRewardProcessing": NumericalRewardProcessing
}

SINK_COMMUNICATION = {
    'socket': SinkComm,
    "serial": SinkSerial
}

TSCH_SCHEDULERS = {
    'Contention Free Scheduler': ContentionFreeScheduler,
    'Hard Coded Scheduler': HardCodedScheduler
}

ROUTING_ALGO = {
    "Dijkstra": Dijkstra
}

from sdwsn_controller.controller.container_controller import ContainerController
from sdwsn_controller.controller.numerical_controller import NumericalController
from sdwsn_controller.controller.controller_usb import USBController
from sdwsn_controller.controller.controller import Controller

CONTROLLERS = {
    "native controller": Controller,
    "container controller": ContainerController,
    "USB controller": USBController,
    "numerical controller": NumericalController
}
# Default values
# get the path of this example
SELF_PATH = os.path.dirname(os.path.abspath(__file__))
# move three levels up
REPO_PATH = os.path.dirname(os.path.dirname(SELF_PATH))
DEFAULT_CONFIG = os.path.normpath(os.path.join(
    REPO_PATH, "etc", "sdwsn-controller.json"))
# DEFAULT_CONFIG = '/etc/sdwsn-controller.json'
DEFAULT_NAME = 'example'
DEFAULT_CONTROLLER_TYPE = "native controller"

# Keys in the JSON configuration file
NAME = 'my_example'
CONTROLLER_TYPE = "controller_type"
MQTT = 'mqtt'
NETWORK = 'network'
SINK_COMM = "sink_comm"
TSCH = 'tsch'
ROUTING = 'routing'
CONTIKI = 'contiki'
DOCKER = "docker"
REINFORCEMENT_LEARNING = "reinforcement_learning"
PERFORMANCE_METRICS = "performance_metrics"


# TODO: Define __str__() with explicit settings for debugging.
class SDWSNControllerConfig:
    """This class represents the configuration of a Hermes audio server.

    Attributes:
        name (str): The name ID of the audio server.
        mqtt (:class:`.MQTTConfig`): The MQTT options of the configuration.
        network (:class:`.NETWORKConfig`): The NETWORK options of the configuration.
        tsch (:class:`.TSCHConfig`): The TSCH options of the configuration.
        routing (:class:`.ROUTINGConfig`): The ROUTING options of the configuration.
        contiki (:class:`.CONTIKIConfig`): The CONTIKI options of the configuration.
        docker (:class:`.DOCKERConfig`): The DOCKER options of the configuration.
    """

    def __init__(self, name='default', controller_type=None, mqtt=None,
                 network=None, sink_comm=None, tsch=None, routing=None,
                 contiki=None, reinforcement_learning=None, docker=None,
                 performance_metrics=None):
        """Initialize a :class:`.SDWSNControllerConfig` object.

        Args:
            name (str): The name ID of the Hermes audio server. Defaults
                to 'default'.
            mqtt (:class:`.MQTTConfig`, optional): The MQTT connection
                settings. Defaults to a default :class:`.MQTTConfig` object.
            network (:class:`.NETWORKConfig`, optional): The NETWORK settings. Defaults
                to a default :class:`.NETWORKConfig` object.
            tsch (:class:`.TSCHConfig`, optional): The TSCH settings. Defaults
                to a default :class:`.TSCHConfig` object.
            routing (:class:`.ROUTINGConfig`, optional): The ROUTING settings. Defaults
                to a default :class:`.ROUTINGConfig` object.
            contiki (:class:`.CONTIKIConfig`, optional): The CONTIKI settings. Defaults
                to a default :class:`.CONTIKIConfig` object.
            docker (:class:`.DOCKERConfig`, optional): The DOCKER settings. Defaults
                to a default :class:`.DOCKERConfig` object.
        """
        self.name = name
        self.controller_type = controller_type

        if mqtt is None:
            self.mqtt = MQTTConfig()
        else:
            self.mqtt = mqtt

        # if network is None:
        #     self.network = NETWORKConfig()
        # else:
        self.network = network

        self.sink_comm = sink_comm

        # if tsch is None:
        #     self.tsch = TSCHConfig()
        # else:
        self.tsch = tsch

        # if routing is None:
        #     self.routing = ROUTINGConfig()
        # else:
        self.routing = routing

        if contiki is None:
            self.contiki = CONTIKIConfig()
        else:
            self.contiki = contiki

        if reinforcement_learning is None:
            self.reinforcement_learning = REINFORCEMENTLEARNINGConfig()
        else:
            self.reinforcement_learning = reinforcement_learning

        if docker is None:
            self.docker = DOCKERConfig()
        else:
            self.docker = docker

        if performance_metrics is None:
            self.performance_metrics = PERFORMANCEMETRICSConfig()
        else:
            self.performance_metrics = performance_metrics

    @classmethod
    def from_json_file(cls, filename=None):
        """Initialize a :class:`.SDWSNControllerConfig` object with settings
        from a JSON file.

        Args:
            filename (str): The filename of a JSON file with the settings.
                Defaults to '/etc/sdwsn-controller.json'.

        Returns:
            :class:`.SDWSNControllerConfig`: An object with the settings
            of the SDWSN controller.

        The :attr:`mqtt` attribute of the :class:`.SDWSNControllerConfig`
        object is initialized with the MQTT connection settings from the
        configuration file, or the default values (hostname 'localhost' and
        port number 1883) if the settings are not specified.

        The :attr:`name` attribute of the :class:`.SDWSNControllerConfig`
        object is initialized with the setting from the configuration file,
        or 'default' is the setting is not specified.

        The :attr:`network` attribute of the :class:`.SDWSNControllerConfig` object is
        initialized with the settings from the configuration file, or not
        enabled when not specified.

        Raises:
            :exc:`ConfigurationFileNotFoundError`: If :attr:`filename` doesn't
                exist.

            :exc:`PermissionError`: If we have no read permissions for
                :attr:`filename`.

            :exc:`JSONDecodeError`: If :attr:`filename` doesn't have a valid
                JSON syntax.

        The JSON file should have the following format:

        {
            "name": "example",
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "authentication": {
                    "username": "foobar",
                    "password": "secretpassword"
                },
                "tls": {
                    "ca_certificates": "",
                    "client_certificate": "",
                    "client_key": ""
                }
            },
            "network": {
                "processing_window": 200,
                "socket": {
                    "host": "127.0.0.1",
                    "port": 123
                }
            },
            "tsch": {
                "scheduler": "Contention Free Scheduler",
                "max_channel": 3,
                "max_slotframe": 500,
                "slot_duration": 10
            },
            "routing": {
                "algo": "Dijkstra"
            },
            "contiki": {
                "simulation_folder": "examples/elise",
                "source": "/Users/fernando/contiki-ng",
                "simulation_script": "cooja-orchestra.csc",
                "port": 60001
            }
        }
        """
        if not filename:
            filename = DEFAULT_CONFIG

        try:
            with Path(filename).open('r') as json_file:
                configuration = json.load(json_file)
        except FileNotFoundError as error:
            raise ConfigurationFileNotFoundError(error.filename)

        return cls(name=configuration.get(NAME, DEFAULT_NAME),
                   controller_type=configuration.get(
                       CONTROLLER_TYPE, DEFAULT_CONTROLLER_TYPE),
                   mqtt=MQTTConfig.from_json(configuration.get(MQTT)),
                   network=NETWORKConfig.from_json(configuration.get(NETWORK)),
                   sink_comm=SINKCOMMConfig.from_json(
                       configuration.get(SINK_COMM)),
                   tsch=TSCHConfig.from_json(configuration.get(TSCH)),
                   routing=ROUTINGConfig.from_json(configuration.get(ROUTING)),
                   contiki=CONTIKIConfig.from_json(configuration.get(CONTIKI)),
                   docker=DOCKERConfig.from_json(configuration.get(DOCKER)),
                   reinforcement_learning=REINFORCEMENTLEARNINGConfig.from_json(
                       configuration.get(REINFORCEMENT_LEARNING)),
                   performance_metrics=PERFORMANCEMETRICSConfig.from_json(
                       configuration.get(PERFORMANCE_METRICS))
                   )
