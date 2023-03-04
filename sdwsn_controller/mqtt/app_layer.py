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
from sdwsn_controller.mqtt.mqtt import MQTTClient

import logging
import json


logger = logging.getLogger('main.'+__name__)


# Topics
NETWORK_RECONFIG = "network/reconfiguration/+"
NEIGHBORS = "network/information/neighbors"
TSCH_SECHEDULES = "network/information/tsch/schedules"
ROUTES = "network/information/routing/routes"
DATA = "network/information/sensed_data"
ENERGY = "network/performance_metrics/energy"
LATENCY = "network/performance_metrics/latency"
PDR = "network/performance_metrics/pdr"


class AppLayer(MQTTClient):
    def __init__(
            self,
            config
    ):
        self.name = "MQTT based application layer"
        super().__init__(config)

    def initialize(self):
        return super().initialize()

    def on_connect(self, client, userdata, flags, result_code):
        """Callback that is called when the audio player connects to the MQTT
        broker."""
        super().on_connect(client, userdata, flags, result_code)
        self.mqtt.subscribe(NETWORK_RECONFIG)
        self.mqtt.message_callback_add(
            NETWORK_RECONFIG, self.network_reconfig_process)
        logger.info('Subscribed to %s topic.', NETWORK_RECONFIG)

    def network_reconfig_process(self):
        """ Callback that is called when the controller receives a
        NETWORK_RECONFIG message on MQTT.
        """
        pass

    def send_energy(self, id, seq, energy):
        message = json.dumps({'id': id,
                              'seq': seq,
                              'energy': energy})

        self.mqtt.publish(ENERGY,
                          message)
        logger.debug('Published message on MQTT topic:')
        logger.debug(f'Topic: {ENERGY}')
        logger.debug(f'Message: {message}')

    def send_latency(self):
        print("sending latency called")

    def send_pdr(self):
        print("sending PDR called")
