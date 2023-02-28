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
DEFAULT_PROC_WINDOW = 200
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 1883
DEFAULT_TSCH_MAX_CHANNEL = 3
DEFAULT_TSCH_MAX_SLOTFRAME = 500

# Keys in the JSON configuration file
NAME = "name"
PROCESSING_WINDOW = 'processing_window'
SOCKET = "socket"
HOST = "host"
PORT = 'port'
TSCH = 'tsch'
TSCH_MAX_CHANNEL = "tsch_max_channel"
TSCH_MAX_SLOTFRAME = "tsch_max_slotframe"


class NETWORKSOCKETConfig:
    """This class represents the authentication settings for a connection to an
    MQTT broker.

    Attributes:
        username (str): The username to authenticate to the MQTT broker. `None`
            if there's no authentication.
        password (str): The password to authenticate to the MQTT broker. Can be
            `None`.
    """

    def __init__(self, host=None, port=None):
        """Initialize a :class:`.MQTTAuthConfig` object.

        Args:
            username (str, optional): The username to authenticate to the MQTT
                broker. `None` if there's no authentication.
            password (str, optional): The password to authenticate to the MQTT
                broker. Can be `None`.

        All arguments are optional.
        """
        self.host = host
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
            "username": "foobar",
            "password": "secretpassword"
        }
        """
        if json_object is None:
            json_object = {}

        return cls(host=json_object.get(HOST, DEFAULT_HOST),
                   port=json_object.get(PORT, DEFAULT_PORT))


class NETWORKConfig:
    """This class represents the configuration for the network.

    Attributes:
        host (str): The hostname or IP address of the MQTT broker.
        port (int): The port number  of the MQTT broker.
        auth (:class:`.MQTTAuthConfig`, optional): The authentication
            settings (username and password) for the MQTT broker.
        tls (:class:`.MQTTTLSConfig`, optional): The TLS settings for the MQTT
            broker.
    """

    def __init__(self,
                 name=None,
                 processing_window=DEFAULT_PROC_WINDOW,
                 socket=None
                 ):
        """Initialize a :class:`.MQTTConfig` object.

        Args:
            host (str, optional): The hostname or IP address of the MQTT
                broker.
            port (int, optional): The port number of the MQTT broker.
            auth (:class:`.MQTTAuthConfig`, optional): The authentication
                settings (username and password) for the MQTT broker. Defaults
                to a default :class:`.MQTTAuthConfig` object.
            tls (:class:`.MQTTTLSConfig`, optional): The TLS settings for the
                MQTT broker. Defaults to a default :class:`.MQTTTLSConfig`
                object.

        All arguments are optional.
        """
        self.name = name
        self.processing_window = processing_window

        if socket is None:
            self.socket = NETWORKSOCKETConfig()
        else:
            self.socket = socket

        # if tsch is None:
        #     self.tsch = NETWORKTSCHConfig()
        # else:
        #     self.tsch = tsch

    @classmethod
    def from_json(cls, json_object=None):
        """Initialize a :class:`.MQTTConfig` object with settings from a JSON
        object.

        Args:
            json_object (optional): The JSON object with the MQTT settings.
                Defaults to {}.

        Returns:
            :class:`.MQTTConfig`: An object with the MQTT settings.

        The JSON object should have the following format:

        {
            "processing_window": 200,
            "socket": {
                "host": "127.0.0.1",
                "port": 123
            },
            "tsch": {
                "tsch_max_channel": 3,
                "tsch_max_slotframe": 500
            }
        }
        """
        if json_object is None:
            json_object = {}

        return cls(
            name=json_object.get(NAME),
            processing_window=json_object.get(
                PROCESSING_WINDOW, DEFAULT_PROC_WINDOW),
            socket=NETWORKSOCKETConfig.from_json(json_object.get(SOCKET))
        )
