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
from abc import ABC, abstractmethod
from paho.mqtt.client import Client


import logging

logger = logging.getLogger(f'main.{__name__}')


class MQTTClient(ABC):

    def __init__(self, config):
        """Initialize an MQTT client.

        Args:
            config (:class:`.ServerConfig`): The configuration of
                the MQTT client.
        """
        self.config = config
        self.mqtt = Client()

        self.initialize()

        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect

    def connect(self):
        """Connect to the MQTT broker defined in the configuration."""
        # Set up MQTT authentication.
        if self.config.mqtt.auth.enabled:
            logger.debug('Setting username and password for MQTT broker.')
            self.mqtt.username_pw_set(self.config.mqtt.auth.username,
                                      self.config.mqtt.auth.password)

        # Set up an MQTT TLS connection.
        if self.config.mqtt.tls.enabled:
            logger.debug(
                'Setting TLS connection settings for MQTT broker.')
            self.mqtt.tls_set(ca_certs=self.config.mqtt.tls.ca_certs,
                              certfile=self.config.mqtt.tls.client_cert,
                              keyfile=self.config.mqtt.tls.client_key)

        logger.debug('Connecting to MQTT broker %s:%s...',
                     self.config.mqtt.host,
                     self.config.mqtt.port)
        self.mqtt.connect(self.config.mqtt.host, self.config.mqtt.port)

    @abstractmethod
    def initialize(self):
        """Initialize the MQTT client."""
        pass

    def start(self):
        """Start the event loop to the MQTT broker so the audio server starts
        listening to MQTT topics and the callback methods are called.
        """
        self.connect()
        logger.debug('Starting MQTT event loop...')
        self.mqtt.loop_start()

    def stop(self):
        """Disconnect from the MQTT broker and terminate the audio connection.
        """
        logger.debug('Disconnecting from MQTT broker...')
        self.mqtt.disconnect()
        logger.debug('Terminating MQTT object...')

    def on_connect(self, client, userdata, flags, result_code):
        """Callback that is called when the client connects to the MQTT broker.
        """
        if result_code == 0:
            logger.info('Connected to MQTT broker %s:%s'
                        ' with result code %s.',
                        self.config.mqtt.host,
                        self.config.mqtt.port,
                        result_code)
        else:
            logger.error(f"MQTT failed to connect, return error code {result_code}")

    def on_disconnect(self, client, userdata, result_code):
        """Callback that is called when the client connects from the MQTT
        broker."""
        # This callback doesn't seem to be called.
        logger.info('Disconnected with result code %s.', result_code)
