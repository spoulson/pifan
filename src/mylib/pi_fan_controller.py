"""
Pi Fan controller class.
"""

from datetime import datetime, timedelta
from functools import reduce
import json
import os
import traceback
from typing import List
from .ipmi_cpu import IpmiCpu
from .ipmi_fan import IpmiFan
from .util import make_slug


class ControllerState:
    """
    Runtime state of PiFanController.
    """
    sample_size: int

    samples: List[float]

    # Epoch seconds.
    last_sample_time: float

    def __init__(self):
        self.sample_size = 3
        self.samples = []
        self.last_sample_time = None

    def add_aggregate_temp(self, value: float) -> float:
        """
        Add a CPU temp value to aggregate average.
        Return new average.
        """
        # Check if aggregate samples are too old.
        if self.last_sample_time is not None:
            last_sample_time2 = datetime.fromtimestamp(self.last_sample_time)
            now = datetime.now()
            threshold_time = now - timedelta(hours=1)
            if last_sample_time2 < threshold_time:
                # Too old, clear samples.
                self.samples = []

        self.samples.append(value)
        self.samples = self.samples[-self.sample_size:]
        agg_value = reduce(
            lambda a, b: a + b,
            self.samples
        ) / len(self.samples)
        self.last_sample_time = datetime.now().timestamp()
        return agg_value

    def set_sample_size(self, sample_size: int) -> None:
        """
        Set sample size.
        """
        self.sample_size = sample_size
        self.samples = self.samples[-sample_size:]

    def restore(self, json_str: str) -> None:
        """
        Restore state from JSON string previously created by dump().
        """
        self.__dict__.update(json.loads(json_str))

    def dump(self) -> str:
        """
        Dump state to JSON string.
        """
        return json.dumps(self.__dict__)


class PiFanController:
    """
    Fan Controller.
    Reads fan and CPU sensors and changes fan speed to optimize noise reduction
    and power consumption.
    """
    name: str

    ipmi_fan: IpmiFan

    ipmi_cpu: IpmiCpu

    interval: int

    ideal_temp: float

    max_temp: float

    easing: str

    dry_run: bool

    state_path: str

    sample_size: int

    def __init__(self, name: str, ipmi_fan: IpmiFan,
                 ipmi_cpu: IpmiCpu) -> None:
        self.name = name
        self.ipmi_fan = ipmi_fan
        self.ipmi_cpu = ipmi_cpu
        self.interval = 10
        self.ideal_temp = 40.0
        self.max_temp = 75.0
        self.max_fan = 100
        self.easing = 'linear'
        self.dry_run = False
        self.sample_size = 3

        if 'TMP' in os.environ:
            self.state_path = os.environ['TMP']
        else:
            self.state_path = '/tmp'

    def _suggest_fan_speed_linear(self, cpu_temp: float) -> int:
        """
        Suggest a fan speed based on linear algorithm.
        """
        offset = cpu_temp - self.ideal_temp
        if offset < 0:
            return 0

        temp_range = self.max_temp - self.ideal_temp
        speed = self.max_fan * offset / temp_range
        return min(self.max_fan, int(speed))

    def _suggest_fan_speed_parabolic(self, cpu_temp: float) -> int:
        """
        Suggest a fan speed based on parabolic curve.
        """
        # https://www.futurelearn.com/info/courses/maths-linear-quadratic/0/steps/12130
        # y = max_temp/(temp_range^2)*x^2
        offset = cpu_temp - self.ideal_temp
        if offset < 0:
            return 0

        temp_range = float(self.max_temp - self.ideal_temp)
        speed = self.max_fan / (temp_range * temp_range) * (offset * offset)
        return min(self.max_fan, int(speed))

    def suggest_fan_speed(self, cpu_temp: float) -> int:
        """
        Suggest a fan speed for a CPU temperature.
        Use selected easing algorithm.
        """
        if self.easing == 'linear':
            return self._suggest_fan_speed_linear(cpu_temp)
        if self.easing == 'parabolic':
            return self._suggest_fan_speed_parabolic(cpu_temp)

        raise Exception(f'Unrecognized easing type "{self.easing}"')

    def state_filename(self) -> str:
        """
        Generate a valid filename for storing controller state.
        """
        slug = 'pifan_' + make_slug(self.name)
        return os.path.join(self.state_path, slug + '.json')

    def load_state(self) -> ControllerState:
        """
        Load state file, if it exists.
        Otherwise, create a new object.
        """
        filename = self.state_filename()
        if os.path.exists(filename):
            # Parse file contents.
            with open(filename, 'r') as state_file:
                state_str = state_file.read()

            state = ControllerState()
            state.restore(state_str)
            state.set_sample_size(self.sample_size)
            return state

        # Return new object.
        state = ControllerState()
        state.set_sample_size(self.sample_size)
        return state

    def save_state(self, state: ControllerState) -> None:
        """
        Save state file.
        """
        filename = self.state_filename()
        state_str = state.dump()
        with open(filename, 'w') as state_file:
            state_file.write(state_str)

    def poll(self, state: ControllerState) -> None:
        """
        Poll fan and CPU sensors and adjust fan speed according to easing
        algorithm.
        """
        poll_start_time = datetime.now()
        print('--- Poll start: ' + poll_start_time.strftime('%x %X'))

        try:
            # Get current CPU temps and aggregate.
            self.ipmi_cpu.read_sensors()
            cpu_temp = self.ipmi_cpu.get_max_cpu_temp()
            agg_cpu_temp = state.add_aggregate_temp(cpu_temp)

            # Save state to file for use with --one mode or if polling was
            # restarted.
            self.save_state(state)

            num_samples = len(state.samples)
            if num_samples < state.sample_size:
                # Need more samples before proceeding.
                print(f'Collected {num_samples}/{state.sample_size} '
                      'samples.')

            else:
                # Set fan speed.
                print(f'Aggregate CPU temperature: {agg_cpu_temp:0.1f}C')
                speed = self.suggest_fan_speed(agg_cpu_temp)
                print(f'Suggested fan speed: {speed}%')

                if not self.dry_run:
                    self.ipmi_fan.set_fan_speed(speed)
                else:
                    print('Dry run mode: not calling set_fan_speed()')

                self.ipmi_fan.read_sensors()

        except Exception:  # pylint: disable=broad-except
            print(traceback.format_exc())

        poll_end_time = datetime.now()
        print('--- Poll end: ' + poll_end_time.strftime('%x %X') + '\n')
