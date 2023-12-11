from datetime import timedelta
import time
from typing import NamedTuple

import gpiod
from gpiod.line import Bias, Edge

from src.utils.utils import TapStatus


class Tap(NamedTuple):
    """Stores information describing a tap event.

    Attributes:
        machine_id: The ID of the machine from which the tap was made.
        timestamp: The timestamp at which the tap was made.
        status: A TapStatus indicating the status of the tap.
    """
    machine_id: str = ''
    timestamp: time.struct_time = 0.0
    status: TapStatus = TapStatus.BAD

    def __iter__(self):
        """Enable iteration over Tap attributes.

        This method allows the Tap instance to be converted to a dictionary.
        """
        for name, _ in self.__annotations__.items():
            yield name, getattr(self, name)


class SelfReleasingGpioLineRequest:
    def __init__(self, chip_path: str, line_offset: int, line_settings: gpiod.LineSettings):
        self.chip_path = chip_path
        self.line_offset = line_offset
        self.line_settings = line_settings
        self.line = None

    def __enter__(self):
        self.line = gpiod.request_lines(
            path=self.chip_path,
            consumer='watch-touch-sensor-line',
            config={self.line_offset: self.line_settings}
            )
        return self.line

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.line:
            self.line.release()