"""This module contains exceptions defined for SDWSN controller."""


class SDWSNControllerError(Exception):
    """Base class for exceptions raised by Hermes Audio Server code.

    By catching this exception type, you catch all exceptions that are
    defined by the Hermes Audio Server code."""


class ConfigurationFileNotFoundError(SDWSNControllerError):
    """Raised when the configuration file is not found."""

    def __init__(self, filename):
        """Initialize the exception with a string representing the filename."""
        self.filename = filename
