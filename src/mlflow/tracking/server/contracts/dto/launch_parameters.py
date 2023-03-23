""" MLFlow Tracking Server Supported Launch Parameters """

from ..types.activity import ActivityType
from .base_model import BaseModel


# pylint: disable=too-few-public-methods
class LaunchParameters(BaseModel):
    """
    MLFlow Tracking Server Supported Launch Parameters (DTO)
    sanity: bool
        If `True` will attempt to ensure needed directories are present on before launching MLFlow.
        MLFlow does not automatically create its own directory structure and will fail to start up.
        When running as an AE5 deployment it is advices to leave this with the default `True`.
    port: str
        The port to start the server listening on.  This is meant to be automatically set by AE5.
    address: str
        The address to start the server listening on.  This is meant to be automatically set by AE5.
    activity: ActivityType
        The command activity type to invoke
    dry_run: bool
        For a supporting command activity type, defines whether to commit changes or report only.
    """

    sanity: bool = False
    port: int = 8086
    address: str = "0.0.0.0"

    activity: ActivityType
    dry_run: bool = False
