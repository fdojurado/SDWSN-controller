"""Module with an MQTT client.
"""
from paho.mqtt.client import Client


class MQTTClient:
    """This class represents an MQTT client for Hermes Audio Server.

    This is an abstract base class. You don't instantiate an object of this
    class, but an object of one of its subclasses.
    """

    def __init__(self, config, verbose):
        """Initialize an MQTT client.

        Args:
            config (:class:`.ServerConfig`): The configuration of
                the MQTT client.
            verbose (bool): Whether or not the MQTT client runs in verbose
                mode.
            logger (:class:`logging.Logger`): The Logger object for logging
                messages.
        """
        self.config = config
        self.verbose = verbose
        self.mqtt = Client()

        self.initialize()

        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_message = self.on_message
        self.connect()

    def connect(self):
        """Connect to the MQTT broker defined in the configuration."""
        # Set up MQTT authentication.
        if self.config.mqtt.auth.enabled:
            print('Setting username and password for MQTT broker.')
            self.mqtt.username_pw_set(self.config.mqtt.auth.username,
                                      self.config.mqtt.auth.password)

        # Set up an MQTT TLS connection.
        # if self.config.mqtt.tls.enabled:
        #     print('Setting TLS connection settings for MQTT broker.')
        #     self.mqtt.tls_set(ca_certs=self.config.mqtt.tls.ca_certs,
        #                       certfile=self.config.mqtt.tls.client_cert,
        #                       keyfile=self.config.mqtt.tls.client_key)

        print('Connecting to MQTT broker %s:%s...',
              self.config.mqtt.host,
              self.config.mqtt.port)
        self.mqtt.connect(self.config.mqtt.host, self.config.mqtt.port)

    def initialize(self):
        """Initialize the MQTT client."""

    def start(self):
        """Start the event loop to the MQTT broker so the audio server starts
        listening to MQTT topics and the callback methods are called.
        """
        print('Starting MQTT event loop...')
        self.mqtt.loop_forever()

    def stop(self):
        """Disconnect from the MQTT broker and terminate the audio connection.
        """
        print('Disconnecting from MQTT broker...')
        self.mqtt.disconnect()

    def on_message(self, client, userdata, msg):
        """ The callback for when a PUBLISH message is received from the server. """
        print('Message published')
        print(msg.topic+" "+str(msg.payload))

    def on_connect(self, client, userdata, flags, result_code):
        """Callback that is called when the client connects to the MQTT broker.
        """
        print('Connected to MQTT broker %s:%s'
              ' with result code %s.',
              self.config.mqtt.host,
              self.config.mqtt.port,
              result_code)

    def on_disconnect(self, client, userdata, flags, result_code):
        """Callback that is called when the client connects from the MQTT
        broker."""
        # This callback doesn't seem to be called.
        print('Disconnected with result code %s.', result_code)
