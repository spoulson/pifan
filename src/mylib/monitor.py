"""
Continuously monitor by polling at an interval.
"""
from datetime import timedelta
import time
from .controller_state import ControllerState
from .pi_fan_controller import PiFanController


class Monitor:
    """
    Continuously monitor by polling at an interval.
    """
    controller: PiFanController

    interval: timedelta

    def __init__(self, controller: PiFanController, interval: timedelta):
        self.controller = controller
        self.interval = interval

    def launch(self, state: ControllerState) -> None:
        """
        Continuously poll fan and CPU sensors and adjust fan speed according
        to easing algorithm.
        """
        while True:
            self.controller.poll(state)

            # Wait for next polling interval.
            poll_start_time = self.controller.poll_start_time
            poll_end_time = self.controller.poll_end_time
            next_poll_time = poll_start_time + self.interval
            if next_poll_time > poll_end_time:
                delay = (next_poll_time - poll_end_time).total_seconds()
                time.sleep(delay)
