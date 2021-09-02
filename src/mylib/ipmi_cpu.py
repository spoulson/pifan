"""
IPMI control of CPU temperatures.
"""

import re
from typing import Dict
from .ipmitool import Ipmitool
from .util import parse_hex


class CpuSensor:
    """
    CPU sensor state.
    """
    name: str

    id: int

    temp: float

    def __init__(self) -> None:
        self.name = ''
        self.id = 0
        self.temp = 0.0

    def __str__(self) -> str:
        return(f'CpuSensor: name={self.name}, id={self.id:#x}, '
               f'temp={self.temp}C')


class IpmiCpu:
    """
    IPMI control of CPU temperatures.
    """
    cpu_map: Dict[str, CpuSensor]

    ipmitool: Ipmitool

    pat_integer = re.compile(r'^(\d+)')

    def __init__(self, host: str, username: str, password: str) -> None:
        self.cpu_map = {}
        self.ipmitool = Ipmitool(host, username, password)

    def discover_sensors(self) -> None:
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

        self.cpu_map = cpu_map
        self.dump_sensors()

    def read_sensors(self) -> None:
        """
        Read current sensor values.
        Store values in self.cpu_map.
        """
        rows = self.ipmitool.sdr_type('temperature')

        for row in rows:
            if len(row) < 2:
                continue

            key = f'{row[0]} ({parse_hex(row[1]):#x})'
            if key in self.cpu_map:
                sensor = self.cpu_map[key]

                # CPU temperature
                match_integer = self.pat_integer.match(row[4])
                if match_integer is not None:
                    sensor.temp = int(match_integer.groups()[0])

        self.dump_sensors()

    def dump_sensors(self) -> None:
        """
        Dump sensors to console.
        """
        names = self.cpu_map.keys()
        for name in sorted(names):
            cpu = self.cpu_map[name]
            print(cpu)

    def get_max_cpu_temp(self) -> float:
        """
        Get maximum of CPU temps.
        """
        temp: float = 0.0

        for key in self.cpu_map:
            sensor = self.cpu_map[key]
            temp = max(temp, sensor.temp)

        return temp
