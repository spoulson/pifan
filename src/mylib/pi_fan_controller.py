"""
Pi Fan controller class.
"""

from datetime import datetime, timedelta
from functools import reduce
import time
import traceback
from typing import List
from .ipmi_cpu import IpmiCpu
from .ipmi_fan import IpmiFan


class PiFanController:
    """
    Fan Controller.
    Reads fan and CPU sensors and changes fan speed to optimize noise reduction
    and power consumption.
    """
    ipmi_fan: IpmiFan

    ipmi_cpu: IpmiCpu

    interval: int

    ideal_temp: float

    max_temp: float

    easing: str

    dry_run: bool

    sample_size: int

    samples: List[float]

    def __init__(self, ipmi_fan: IpmiFan, ipmi_cpu: IpmiCpu) -> None:
        self.ipmi_fan = ipmi_fan
        self.ipmi_cpu = ipmi_cpu
        self.interval = 10
        self.ideal_temp = 40.0
        self.max_temp = 75.0
        self.max_fan = 100
        self.easing = 'linear'
        self.dry_run = False
        self.sample_size = 3
        self.samples = []

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

    def add_aggregate_temp(self, value: float):
        """
        Add a CPU temp value to aggregate average.
        Return new average.
        """
        self.samples.append(value)
        self.samples = self.samples[-self.sample_size:]
        return reduce(lambda a, b: a + b, self.samples) / len(self.samples)

    def monitor(self) -> None:
        """
        Monitor fan and CPU sensors and adjust fan speed according to easing
        algorithm.
        Runs endlessly.
        """
        print()

        while True:
            poll_start_time = datetime.now()
            print('--- Poll start: ' + poll_start_time.strftime('%x %X'))

            try:
                self.ipmi_cpu.read_sensors()
                cpu_temp = self.ipmi_cpu.get_max_cpu_temp()
                agg_cpu_temp = self.add_aggregate_temp(cpu_temp)

                num_samples = len(self.samples)
                if num_samples < self.sample_size:
                    # Need more samples before proceeding.
                    print(f'Collected {num_samples}/{self.sample_size} '
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

            # Wait for next polling interval.
            next_poll_time = poll_start_time + timedelta(seconds=self.interval)
            delay = (next_poll_time - poll_end_time).total_seconds()
            if delay > 0:
                time.sleep(delay)
