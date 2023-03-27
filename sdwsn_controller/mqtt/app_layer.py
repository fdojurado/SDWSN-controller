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


logger = logging.getLogger(f'main.{__name__}')


# Topics
NETWORK_RECONFIG = "network/reconfiguration/+"
NEIGHBORS = "network/information/neighbors"
RL = "network/information/rl"
TSCH_SECHEDULES = "network/information/tsch/schedules"
ROUTES = "network/information/routing/routes"
DATA = "network/information/sensed_data"
ENERGY = "network/performance_metrics/energy"
LATENCY = "network/performance_metrics/latency"
PDR = "network/performance_metrics/pdr"
USER_REQ_GET = "network/user_requirements/get"
USER_REQ_SET = "network/user_requirements/set"
USER_REQ_CURRENT = "network/user_requirements/set"


class AppLayer(MQTTClient):
    def __init__(
            self,
            config,
            controller,
    ):
        self.name = "MQTT based application layer"
        self.controller = controller
        super().__init__(config)

    def initialize(self):
        return super().initialize()

    def on_connect(self, client, userdata, flags, result_code):
        """Callback that is called when the audio player connects to the MQTT
        broker."""
        super().on_connect(client, userdata, flags, result_code)
        self.mqtt.subscribe(NETWORK_RECONFIG)
        self.mqtt.subscribe(USER_REQ_SET)
        self.mqtt.subscribe(USER_REQ_GET)
        self.mqtt.message_callback_add(
            NETWORK_RECONFIG, self.network_reconfig_process)
        self.mqtt.message_callback_add(
            USER_REQ_SET, self.user_requirements_set)
        self.mqtt.message_callback_add(
            USER_REQ_GET, self.user_requirements_get)
        # logger.info('Subscribed to %s topic.', NETWORK_RECONFIG)

    def user_requirements_set(self, client, userdata, message):
        # print("user requirements received")
        data = dict(
            topic=message.topic,
            payload=message.payload.decode()
        )
        payload = json.loads(data['payload'])
        # print(payload)
        self.controller.alpha = payload['alpha']
        self.controller.beta = payload['beta']
        self.controller.delta = payload['delta']

    def user_requirements_get(self, client, userdata, message):
        # print("get requirements received")
        message = json.dumps({'alpha': self.controller.alpha,
                              'beta': self.controller.beta,
                              'delta': self.controller.delta})
        self.mqtt.publish(USER_REQ_CURRENT,
                          message)

    def network_reconfig_process(self):
        """ Callback that is called when the controller receives a
        NETWORK_RECONFIG message on MQTT.
        """
        pass

    def send_energy(self, id, seq, energy):
        # message = json.dumps({'id': id,
        #                       'seq': seq,
        #                       'energy': energy})

        # self.mqtt.publish(ENERGY,
        #                   message)
        # logger.debug('Published message on MQTT topic:')
        # logger.debug(f'Topic: {ENERGY}')
        # logger.debug(f'Message: {message}')
        pass

    def send_rl_info(self, data):
        message = json.dumps(data)
        self.mqtt.publish(RL,
                          message)
        # logger.debug('Published message on MQTT topic:')
        # logger.debug(f'Topic: {RL}')
        # logger.debug(f'Message: {message}')

    def send_latency(self, id, seq, delay):
        # message = json.dumps({'id': id,
        #                       'seq': seq,
        #                       'delay': delay})
        # self.mqtt.publish(LATENCY, message)
        # logger.debug('Published message on MQTT topic:')
        # logger.debug(f'Topic: {LATENCY}')
        # logger.debug(f'Message: {message}')
        pass

    def send_pdr(self, id, seq, pdr):
        # message = json.dumps({'id': id,
        #                       'seq': seq,
        #                       'pdr': pdr})
        # self.mqtt.publish(PDR, message)
        # logger.debug('Published message on MQTT topic:')
        # logger.debug(f'Topic: {PDR}')
        # logger.debug(f'Message: {message}')
        pass
