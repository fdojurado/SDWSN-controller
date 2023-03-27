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
DEFAULT_MAX_CHANNEL = 3
DEFAULT_MAX_SLOTFRAME = 70
DEFAULT_SLOT_DURATION = 10

# Keys in the JSON configuration file
SCHEDULER = "scheduler"
MAX_CHANNEL = "max_channel"
MAX_SLOTFRAME = "max_slotframe"
SLOT_DURATION = "slot_duration"


class TSCHConfig:
    """This class represents the authentication settings for a connection to an
    MQTT broker.

    Attributes:
        username (str): The username to authenticate to the MQTT broker. `None`
            if there's no authentication.
        password (str): The password to authenticate to the MQTT broker. Can be
            `None`.
    """

    def __init__(self, scheduler=None, max_channel=None,
                 max_slotframe=None, slot_duration=None):
        """Initialize a :class:`.MQTTAuthConfig` object.

        Args:
            username (str, optional): The username to authenticate to the MQTT
                broker. `None` if there's no authentication.
            password (str, optional): The password to authenticate to the MQTT
                broker. Can be `None`.

        All arguments are optional.
        """
        self.scheduler = scheduler
        self.max_channel = max_channel
        self.max_slotframe = max_slotframe
        self.slot_duration = slot_duration

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

        return cls(scheduler=json_object.get(SCHEDULER),
                   max_channel=json_object.get(
                       MAX_CHANNEL, DEFAULT_MAX_CHANNEL),
                   max_slotframe=json_object.get(
                       MAX_SLOTFRAME, DEFAULT_MAX_SLOTFRAME),
                   slot_duration=json_object.get(
                       SLOT_DURATION, DEFAULT_SLOT_DURATION))
