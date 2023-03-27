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
import numpy as np
# Default values
DEFAULT_ENERGY_MIN = 0
DEFAULT_ENERGY_MAX = 5000
DEFAULT_ENERGY_NORM_OFFSET = 0.0

DEFAULT_DELAY_MIN = 0
DEFAULT_DELAY_MAX = 15000
DEFAULT_DELAY_NORM_OFFSET = 0.0

DEFAULT_PDR_MIN = 0
DEFAULT_PDR_MAX = 1
DEFAULT_PDR_NORM_OFFSET = 0.0

# Keys in the JSON configuration file
ENERGY = "energy"
WEIGHTS = "weights"
MIN = "min"
MAX = "max"
NORM_OFFSET = "norm_offset"
DELAY = "delay"
PDR = "pdr"


class PDRConfig:
    """This class represents the authentication settings for a connection to an
    MQTT broker.

    Attributes:
        username (str): The username to authenticate to the MQTT broker. `None`
            if there's no authentication.
        password (str): The password to authenticate to the MQTT broker. Can be
            `None`.
    """

    def __init__(self, min=None, max=None, norm_offset=None, weights=None):
        """Initialize a :class:`.MQTTAuthConfig` object.

        Args:
            username (str, optional): The username to authenticate to the MQTT
                broker. `None` if there's no authentication.
            password (str, optional): The password to authenticate to the MQTT
                broker. Can be `None`.

        All arguments are optional.
        """
        self.min = min
        self.max = max
        self.norm_offset = norm_offset

        if weights is not None:
            self.weights = np.array(weights)

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

        return cls(
            min=json_object.get(MIN, DEFAULT_PDR_MIN),
            max=json_object.get(MAX, DEFAULT_PDR_MAX),
            norm_offset=json_object.get(
                NORM_OFFSET, DEFAULT_PDR_NORM_OFFSET),
            weights=json_object.get(WEIGHTS)
        )


class DELAYConfig:
    """This class represents the authentication settings for a connection to an
    MQTT broker.

    Attributes:
        username (str): The username to authenticate to the MQTT broker. `None`
            if there's no authentication.
        password (str): The password to authenticate to the MQTT broker. Can be
            `None`.
    """

    def __init__(self, min=None, max=None, norm_offset=None, weights=None):
        """Initialize a :class:`.MQTTAuthConfig` object.

        Args:
            username (str, optional): The username to authenticate to the MQTT
                broker. `None` if there's no authentication.
            password (str, optional): The password to authenticate to the MQTT
                broker. Can be `None`.

        All arguments are optional.
        """
        self.min = min
        self.max = max
        self.norm_offset = norm_offset

        if weights is not None:
            self.weights = np.array(weights)

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

        return cls(
            min=json_object.get(MIN, DEFAULT_DELAY_MIN),
            max=json_object.get(MAX, DEFAULT_DELAY_MAX),
            norm_offset=json_object.get(
                NORM_OFFSET, DEFAULT_DELAY_NORM_OFFSET),
            weights=json_object.get(WEIGHTS)
        )


class ENERGYConfig:
    """This class represents the authentication settings for a connection to an
    MQTT broker.

    Attributes:
        username (str): The username to authenticate to the MQTT broker. `None`
            if there's no authentication.
        password (str): The password to authenticate to the MQTT broker. Can be
            `None`.
    """

    def __init__(self, min=None, max=None, norm_offset=None, weights=None):
        """Initialize a :class:`.MQTTAuthConfig` object.

        Args:
            username (str, optional): The username to authenticate to the MQTT
                broker. `None` if there's no authentication.
            password (str, optional): The password to authenticate to the MQTT
                broker. Can be `None`.

        All arguments are optional.
        """
        self.min = min
        self.max = max
        self.norm_offset = norm_offset

        if weights is not None:
            self.weights = np.array(weights)

    @ classmethod
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

        return cls(
            min=json_object.get(MIN, DEFAULT_ENERGY_MIN),
            max=json_object.get(MAX, DEFAULT_ENERGY_MAX),
            norm_offset=json_object.get(
                NORM_OFFSET, DEFAULT_ENERGY_NORM_OFFSET),
            weights=json_object.get(WEIGHTS)
        )


class PERFORMANCEMETRICSConfig:
    """This class represents the authentication settings for a connection to an
    MQTT broker.

    Attributes:
        username (str): The username to authenticate to the MQTT broker. `None`
            if there's no authentication.
        password (str): The password to authenticate to the MQTT broker. Can be
            `None`.
    """

    def __init__(self, energy=None, delay=None, pdr=None):
        """Initialize a :class:`.MQTTAuthConfig` object.

        Args:
            username (str, optional): The username to authenticate to the MQTT
                broker. `None` if there's no authentication.
            password (str, optional): The password to authenticate to the MQTT
                broker. Can be `None`.

        All arguments are optional.
        """
        if energy is None:
            self.energy = ENERGYConfig()
        else:
            self.energy = energy

        if delay is None:
            self.delay = DELAYConfig()
        else:
            self.delay = delay

        if pdr is None:
            self.pdr = PDRConfig()
        else:
            self.pdr = pdr

    @ classmethod
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

        return cls(
            energy=ENERGYConfig.from_json(json_object.get(ENERGY)),
            delay=DELAYConfig.from_json(json_object.get(DELAY)),
            pdr=PDRConfig.from_json(json_object.get(PDR))
        )
