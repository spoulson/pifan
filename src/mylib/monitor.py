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

    count: int

    def __init__(self, controller: PiFanController, interval: timedelta,
                 count: int):
        self.controller = controller
        self.interval = interval
        self.count = count

    def launch(self, state: ControllerState) -> None:
        """
        Continuously poll fan and CPU sensors and adjust fan speed according
        to easing algorithm.
        """
        counter: int = 0

        while True:
            self.controller.poll(state)

            # Stop after a defined poll limit.
            counter += 1
            if self.count > 0 and counter >= self.count:
                break

            # Wait for next polling interval.
            poll_start_time = self.controller.poll_start_time
            poll_end_time = self.controller.poll_end_time
            next_poll_time = poll_start_time + self.interval
            if next_poll_time > poll_end_time:
                delay = (next_poll_time - poll_end_time).total_seconds()
                time.sleep(delay)
