"""Classes for the configuration of hermes-audio-server."""
import json
from pathlib import Path

from controller.config.routing import RoutingConfig
from controller.config.mqtt import MQTTConfig
from controller.config.serial import SerialConfig
# from hermes_audio_server.exceptions import ConfigurationFileNotFoundError


# Default values
DEFAULT_CONFIG = 'controller/etc/sdn-controller-config.json'
# DEFAULT_SITE = 'default'

# Keys in the JSON configuration file
# SITE = 'site'
MQTT = 'mqtt'
SERIAL = 'serial'
ROUTING = 'routing'


# TODO: Define __str__() with explicit settings for debugging.
class ServerConfig:
    """This class represents the configuration of a Hermes audio server.

    Attributes:
        site (str): The site ID of the audio server.
        mqtt (:class:`.MQTTConfig`): The MQTT options of the configuration.
        vad (:class:`.VADConfig`): The VAD options of the configuration.
    """

    def __init__(self, site='default', mqtt=None, serial=None, routing=None):
        """Initialize a :class:`.ServerConfig` object.

        Args:
            site (str): The site ID of the Hermes audio server. Defaults
                to 'default'.
            mqtt (:class:`.MQTTConfig`, optional): The MQTT connection
                settings. Defaults to a default :class:`.MQTTConfig` object.
            vad (:class:`.VADConfig`, optional): The VAD settings. Defaults
                to a default :class:`.VADConfig` object, which disables voice
                activity detection.
        """
        if mqtt is None:
            self.mqtt = MQTTConfig()
        else:
            self.mqtt = mqtt

        if serial is None:
            self.serial = SerialConfig()
        else:
            self.serial = serial
        
        if routing is None:
            self.routing = RoutingConfig()
        else:
            self.routing = routing

        self.site = site

    @classmethod
    def from_json_file(cls, filename=None, iotlab=None):
        """Initialize a :class:`.ServerConfig` object with settings
        from a JSON file.

        Args:
            filename (str): The filename of a JSON file with the settings.
                Defaults to '/etc/hermes-audio-server'.

        Returns:
            :class:`.ServerConfig`: An object with the settings
            of the Hermes Audio Server.

        The :attr:`mqtt` attribute of the :class:`.ServerConfig`
        object is initialized with the MQTT connection settings from the
        configuration file, or the default values (hostname 'localhost' and
        port number 1883) if the settings are not specified.

        The :attr:`site` attribute of the :class:`.ServerConfig`
        object is initialized with the setting from the configuration file,
        or 'default' is the setting is not specified.

        The :attr:`vad` attribute of the :class:`.ServerConfig` object is
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
            "site": "default",
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
            "vad": {
                "mode": 0,
                "silence": 2,
                "status_messages": true
            }
        }
        """
        if iotlab:
            global SERIAL
            SERIAL = 'iotlab'
        if not filename:
            filename = DEFAULT_CONFIG

        try:
            with Path(filename).open('r') as json_file:
                print('opening json file')
                configuration = json.load(json_file)
                print(configuration)
        except FileNotFoundError as error:
            raise ConfigurationFileNotFoundError(error.filename)

        return cls(mqtt=MQTTConfig.from_json(configuration.get(MQTT)),
                   routing=RoutingConfig.from_json(configuration.get(ROUTING)),
                   serial=SerialConfig.from_json(configuration.get(SERIAL)))
