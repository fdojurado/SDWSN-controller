"""Class for the VAD configuration of hermes-audio-server."""
# Default values
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 60001

# Keys in the JSON configuration file
HOST = 'host'
PORT = 'port'


# TODO: Define __str__() for each class with explicit settings for debugging.
class SerialConfig:
    """This class represents the VAD settings for Hermes Audio Recorder.

    Attributes:
        enabled (bool): Whether or not VAD is enabled.
        mode (int): Aggressiveness mode for VAD. 0 is the least aggressive
            about filtering out non-speech, 3 is the most aggressive.
        silence (int): How much silence (no speech detected) in seconds has
            to go by before Hermes Audio Recorder considers it the end of a
            voice message.
        status_messages (bool): Whether or not Hermes Audio Recorder sends
            messages on MQTT when it detects the start or end of a voice
            message.
    """

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
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
        self.host = host
        self.port = port

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
            ret = cls(host=json_object.get(HOST, DEFAULT_HOST),
                      port=json_object.get(PORT, DEFAULT_PORT))

        return ret
