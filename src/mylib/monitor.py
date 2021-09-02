"""
Continuously monitor by polling at an interval.
"""
from datetime import datetime, timedelta
import time
from .pi_fan_controller import ControllerState, PiFanController


class Monitor:
    """
    Continuously monitor by polling at an interval.
    """
    controller: PiFanController

    state: ControllerState

    interval: timedelta

    def __init__(self, controller: PiFanController, state: ControllerState,
                 interval: timedelta):
        self.controller = controller
        self.state = state
        self.interval = interval

    def launch(self) -> None:
        """
        Continuously poll fan and CPU sensors and adjust fan speed according
        to easing algorithm.
        """
        # Prepare state by loading from file, if exists.
        state = self.controller.load_state()

        while True:
            poll_start_time = datetime.now()
            self.controller.poll(state)

            # Wait for next polling interval.
            poll_end_time = datetime.now()
            next_poll_time = poll_start_time + self.interval
            delay = (next_poll_time - poll_end_time).total_seconds()
            if delay > 0:
                time.sleep(delay)
