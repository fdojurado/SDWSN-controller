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

# Default values
DEFAULT_IMAGE = "contiker/contiki-ng"
DEFAULT_SCRIPT_FOLDER = "examples/elise"
DEFAULT_SIM_SCRIPT = "cooja-orchestra.csc"
DEFAULT_TARGET = "/home/user/contiki-ng"
DEFAULT_PRIVILEGED = True
DEFAULT_DETACH = True
DEFAULT_PORT = 60001

# Keys in the JSON configuration file
IMAGE = "image"
SCRIPT_FOLDER = "script_folder"
TARGET = "target"
CONTIKI = "contiki"
SIMULATION_SCRIPT = "simulation_script"
PRIVILEGED = "privileged"
DETACH = "detach"
PORT = "port"


class DOCKERConfig:
    """This class represents the authentication settings for a connection to an
    MQTT broker.

    Attributes:
        username (str): The username to authenticate to the MQTT broker. `None`
            if there's no authentication.
        password (str): The password to authenticate to the MQTT broker. Can be
            `None`.
    """

    def __init__(self, image=None, script_folder=None, target=None,
                 contiki=None, simulation_script=None,
                 privileged=None, detach=None, port=None):
        """Initialize a :class:`.MQTTAuthConfig` object.

        Args:
            username (str, optional): The username to authenticate to the MQTT
                broker. `None` if there's no authentication.
            password (str, optional): The password to authenticate to the MQTT
                broker. Can be `None`.

        All arguments are optional.
        """
        self.image = image
        self.script_folder = script_folder
        self.target = target
        self.contiki = contiki
        self.simulation_script = simulation_script

        if privileged == "true":
            self.privileged = True
        else:
            self.privileged = privileged

        if detach == "true":
            self.detach = True
        else:
            self.detach = detach

        self.port = port

    @classmethod
    def from_json(cls, json_object=None):
        """Initialize a :class:`.MQTTAuthConfig` object with settings from a
        JSON object.

        Args:
            json_object (optional): The JSON object with the MQTT
                authentication settings. Defaults to {}.

        Returns:
            :class:`.MQTTAuthConfig`: An object with the MQTT authentication
            settings.

        The JSON object should have the following format:

        {
            "scheduler": "Contention Free Scheduler",
            "max_channel": 3,
            "max_slotframe": 500,
            "slot_duration": 10
        }
        """
        if json_object is None:
            json_object = {}

        return cls(image=json_object.get(IMAGE, DEFAULT_IMAGE),
                   script_folder=json_object.get(
                       SCRIPT_FOLDER, DEFAULT_SCRIPT_FOLDER),
                   target=json_object.get(TARGET, DEFAULT_TARGET),
                   contiki=json_object.get(CONTIKI),
                   simulation_script=json_object.get(
                       SIMULATION_SCRIPT, DEFAULT_SIM_SCRIPT),
                   privileged=json_object.get(
                       PRIVILEGED, DEFAULT_PRIVILEGED),
                   detach=json_object.get(
                       DETACH, DEFAULT_DETACH),
                   port=json_object.get(
                       PORT, DEFAULT_PORT))
