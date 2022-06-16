"""Module with an MQTT client.
It requires:
    - pip3 install paho-mqtt
    - brew install mosquitto
To run the server (macOS):
/usr/local/sbin/mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf -p 1884

To publish a message using mosquitto:

mosquitto_pub -h 127.0.0.1 -m "mst" -t alg -d -p 1884
"""

from paho.mqtt.client import Client

MQTT_TOPIC = [("alg", 0), ("control", 0), ("data", 0)]


class MQTTClient():
    """This class represents an MQTT client for ELISE."""

    def __init__(self, config, verbose, routing_alg_queue):
        """Initialize an MQTT client.

        Args:
            config (:class:`.ServerConfig`): The configuration of
                the MQTT client.
            verbose (bool): Whether or not the MQTT client runs in verbose
                mode.
        """
        self.config = config
        self.verbose = verbose
        self.routing_alg_queue = routing_alg_queue
        self.mqtt = Client()

        self.initialize()

        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_disconnect = self.on_disconnect
        self.mqtt.on_message = self.on_message

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
        print('Message received')
        payload = msg.payload.decode("utf-8")
        print(msg.topic+" "+payload)
        if(msg.topic == "alg"):
            # Send the message to the routing algorithm
            self.routing_alg_queue.put(payload)

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

    def run(self):
        self.connect()
        self.mqtt.subscribe(MQTT_TOPIC)

        rc = 0
        while rc == 0:
            rc = self.mqtt.loop_start()
        return rc
