"""Class for the VAD configuration of hermes-audio-server."""
# Default values for the routing
DEFAULT_PROTOCOL = 'dijkstra'
DEFAULT_TIME = 10

PROTOCOL = 'host'
TIME = 'time'


class RoutingConfig:

    def __init__(self, protocol=DEFAULT_PROTOCOL, time=DEFAULT_TIME):
        """Initialize a :class:`.SerialConfig` object.

        Args:
            enabled (bool): Whether or not VAD is enabled. Defaults to False.
            mode (int): Aggressiveness mode for VAD. Defaults to 0.
            silence (int): How much silence (no speech detected) in seconds has
                to go by before Hermes Audio Recorder considers it the end of a
                voice message. Defaults to 2.
            status_messages (bool): Whether or not Hermes Audio Recorder sends
                messages on MQTT when it detects the start or end of a voice
                message. Defaults to False.

        All arguments are optional.
        """
        self.protocol = protocol
        self.time = time

    @classmethod
    def from_json(cls, json_object=None):
        """Initialize a :class:`.SerialConfig` object with settings from a
        JSON object.

        Args:
            json_object (optional): The JSON object with the VAD settings.
                Defaults to {}.

        Returns:
            :class:`.SerialConfig`: An object with the VAD settings.

        The JSON object should have the following format:

        {
            "mode": 0,
            "silence": 2,
            "status_messages": true
        }
        """
        if json_object is None:
            ret = cls(enabled=False)
        else:
            ret = cls(protocol=json_object.get(PROTOCOL, DEFAULT_PROTOCOL),
                      time=json_object.get(TIME, DEFAULT_TIME))

        return ret
