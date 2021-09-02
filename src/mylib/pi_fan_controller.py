"""
Pi Fan controller class.
"""

from datetime import datetime
import os
import traceback
from .controller_state import ControllerState
from .ipmi_cpu import IpmiCpu
from .ipmi_fan import IpmiFan
from .util import make_slug


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

    poll_start_time: datetime

    poll_end_time: datetime

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
        self.poll_start_time = datetime.fromtimestamp(0)
        self.poll_end_time = datetime.fromtimestamp(0)

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
        return os.path.join(self.state_path, slug + '.dat')

    def load_state(self) -> ControllerState:
        """
        Load state file, if it exists.
        Otherwise, create a new object.
        """
        filename = self.state_filename()
        if os.path.exists(filename):
            # Parse file contents.
            with open(filename, 'rb') as state_file:
                state_buf = state_file.read()

            state = ControllerState()
            state.restore(state_buf)
            state.set_sample_size(self.sample_size)
            print(f'Loaded state from {filename}')
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
        state_buf = state.dump()
        with open(filename, 'wb') as state_file:
            state_file.write(state_buf)

    def poll(self, state: ControllerState) -> None:
        """
        Poll fan and CPU sensors and adjust fan speed according to easing
        algorithm.
        """
        # Discover sensors if not set in state.
        if state.fan_map is None or state.cpu_map is None:
            print('--- Discover sensors')
            self.ipmi_fan.discover_sensors(state)
            self.ipmi_cpu.discover_sensors(state)
            self.save_state(state)

        self.poll_start_time = datetime.now()
        print('\n--- Poll start: ' + self.poll_start_time.strftime('%x %X'))

        try:
            # Get current CPU temps and aggregate.
            self.ipmi_cpu.read_sensors(state)
            cpu_temp = self.ipmi_cpu.get_max_cpu_temp(state)
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

                self.ipmi_fan.read_sensors(state)

        except Exception:  # pylint: disable=broad-except
            print(traceback.format_exc())

        self.poll_end_time = datetime.now()
        print('--- Poll end: ' + self.poll_end_time.strftime('%x %X'))
