"""
Pi Fan controller class.
"""

import time
import traceback
from .ipmi_cpu import IpmiCpu
from .ipmi_fan import IpmiFan

class PiFanController:
    """
    Fan Controller.
    """

    def __init__(self, ipmi_fan: IpmiFan, ipmi_cpu: IpmiCpu) -> None:
        self.ipmi_fan = ipmi_fan
        self.ipmi_cpu = ipmi_cpu
        self.ideal_temp = 40.0
        self.max_temp = 75.0
        self.max_fan = 100
        self.easing = 'linear'

    def suggest_fan_speed_linear(self, cpu_temp: float) -> int:
        """
        Suggest a fan speed based on linear formula.
        """
        offset = cpu_temp - self.ideal_temp
        if offset < 0:
            return 0

        temp_range = self.max_temp - self.ideal_temp
        speed = self.max_fan * offset / temp_range
        print(f'suggest_fan_speed_linear: {speed}')
        return min(self.max_fan, int(speed))

    def suggest_fan_speed_parabolic(self, cpu_temp: float) -> int:
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
        print(f'suggest_fan_speed_parabolic: {speed}')
        return min(self.max_fan, int(speed))

    def suggest_fan_speed(self, cpu_temp: float) -> int:
        if self.easing == 'linear':
            return self.suggest_fan_speed_linear(cpu_temp)
        if self.easing == 'parabolic':
            return self.suggest_fan_speed_parabolic(cpu_temp)

        raise Exception(f'Unrecognized easing type "{self.easing}"')

    def monitor(self) -> None:
        while True:
            try:
                cpu_temp = max(self.ipmi_fan.get_cpu_temps())
                print(f'cpu_temp: {cpu_temp}')
                speed = self.suggest_fan_speed(cpu_temp)
                print(f'speed: {speed}')
                self.ipmi_fan.set_fan_speed(speed)
            except:
                print(traceback.format_exc())

            time.sleep(1)
