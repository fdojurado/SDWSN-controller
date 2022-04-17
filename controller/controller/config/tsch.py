"""Class for the VAD configuration of hermes-audio-server."""
# Default values for TSCH
DEFAULT_SLOTFRAME_SIZE = 17
DEFAULT_NUM_CHANNELS = 4


SLOTFRAME_SIZE = 'slotframe_size'
NUM_CHANNELS = 'num_of_channels'


class TSCHConfig:

    def __init__(self, slotframe_size=DEFAULT_SLOTFRAME_SIZE, num_of_channels=DEFAULT_NUM_CHANNELS):
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
        self.slotframe_size = slotframe_size
        self.num_of_channels = num_of_channels

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
            ret = cls(slotframe_size=json_object.get(SLOTFRAME_SIZE, DEFAULT_SLOTFRAME_SIZE),
                      num_of_channels=json_object.get(NUM_CHANNELS, DEFAULT_NUM_CHANNELS))

        return ret
