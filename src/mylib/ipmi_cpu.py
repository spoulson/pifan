"""
IPMI control of CPU temperatures.
"""

import re
from typing import Dict
from .controller_state import ControllerState
from .cpu_sensor import CpuSensor
from .ipmitool import Ipmitool
from .util import parse_hex


class IpmiCpu:
    """
    IPMI control of CPU temperatures.
    """
    ipmitool: Ipmitool

    pat_integer = re.compile(r'^(\d+)')

    def __init__(self, host: str, username: str, password: str) -> None:
        self.ipmitool = Ipmitool(host, username, password)

    def discover_sensors(self, state: ControllerState) -> None:
        """
        Query IPMI for list of CPUs.
        Must call this method first before using this class.
        """
        rows = self.ipmitool.sdr_type('temperature')

        # Filter CPU temp sensors.
        cpu_map: Dict[str, CpuSensor] = {}

        for row in rows:
            name = row[0]
            if name != 'Temp':
                continue

            sensor = CpuSensor()
            sensor.name = name
            sensor.id = parse_hex(row[1])

            # CPU temperature
            match_integer = self.pat_integer.match(row[4])
            if match_integer is not None:
                sensor.temp = int(match_integer.groups()[0])

            print(f'Found CPU temperature sensor: {name} ({sensor.id:#x})')
            key = f'{name} ({sensor.id:#x})'
            cpu_map[key] = sensor

        state.cpu_map = cpu_map
        self.dump_sensors(state)

    def read_sensors(self, state: ControllerState) -> None:
        """
        Read current sensor values.
        Store values in state.
        """
        rows = self.ipmitool.sdr_type('temperature')

        for row in rows:
            if len(row) < 2:
                continue

            key = f'{row[0]} ({parse_hex(row[1]):#x})'
            if key in state.cpu_map:
                sensor = state.cpu_map[key]

                # CPU temperature
                match_integer = self.pat_integer.match(row[4])
                if match_integer is not None:
                    sensor.temp = int(match_integer.groups()[0])

        self.dump_sensors(state)

    def dump_sensors(self, state: ControllerState) -> None:
        """
        Dump sensors to console.
        """
        names = state.cpu_map.keys()
        for name in sorted(names):
            cpu = state.cpu_map[name]
            print(cpu)

    def get_max_cpu_temp(self, state: ControllerState) -> float:
        """
        Get maximum of CPU temps.
        """
        temp: float = 0.0

        for key in state.cpu_map:
            sensor = state.cpu_map[key]
            temp = max(temp, sensor.temp)

        return temp
