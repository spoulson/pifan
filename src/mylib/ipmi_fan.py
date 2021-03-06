"""
IPMI control of chassis fans.
"""

import re
from typing import Dict
from .controller_state import ControllerState
from .fan_sensor import FanSensor
from .ipmitool import Ipmitool
from .util import parse_hex


class IpmiFan:
    """
    IPMI control of chassis fans.
    """
    ipmitool: Ipmitool

    pat_fan = re.compile(r'^Fan\d+$')
    pat_name = re.compile(r'^(.+) \(')
    pat_integer = re.compile(r'^(\d+)')

    def __init__(self, host: str, username: str, password: str) -> None:
        self.ipmitool = Ipmitool(host, username, password)

    def discover_sensors(self, state: ControllerState) -> None:
        """
        Query IPMI for list of chassis fans.
        Must call this method first before using this class.
        """
        rows = self.ipmitool.sdr_type('fan')

        # Filter fan sensors.
        fan_map: Dict[str, FanSensor] = {}

        for row in rows:
            name = row[0]
            if self.pat_fan.match(name) is None:
                continue

            sensor = FanSensor()
            sensor.name = name
            sensor.id = parse_hex(row[1])

            print(f'Found fan sensor: {name} ({sensor.id:#x})')
            fan_map[name] = sensor

        state.fan_map = fan_map

        # Read sensor values.
        self.read_sensors(state)

    def read_sensors(self, state: ControllerState) -> None:
        """
        Read current sensor values.
        Store values in state.
        """
        fan_names = list(state.fan_map.keys())
        result = self.ipmitool.sdr_get(fan_names)

        # Sensor ID              : Fan1 (0x30)
        #  Entity ID             : 7.1 (System Board)
        #  Sensor Type (Threshold)  : Fan (0x04)
        #  Sensor Reading        : 2400 (+/- 120) RPM
        #  Status                : ok
        #  Nominal Reading       : 10080.000
        #  Normal Minimum        : 16680.000
        #  Normal Maximum        : 23640.000
        #  Lower critical        : 600.000
        #  Lower non-critical    : 840.000
        #  Positive Hysteresis   : 120.000
        #  Negative Hysteresis   : 120.000
        #  Minimum sensor range  : Unspecified
        #  Maximum sensor range  : Unspecified
        #  Event Message Control : Per-threshold
        #  Readable Thresholds   : lcr lnc
        #  Settable Thresholds   :
        #  Threshold Read Mask   : lcr lnc
        #  Assertion Events      :
        #  Assertions Enabled    : lnc- lcr-
        #  Deassertions Enabled  : lnc- lcr-

        for key in result:
            # Sensor name.
            match_name = self.pat_name.match(key)
            if match_name is None:
                continue

            name = match_name.groups()[0]
            sensor_data = result[key]
            sensor = state.fan_map[name]

            if 'Sensor Reading' in sensor_data:
                value = sensor_data['Sensor Reading']
                match_integer = self.pat_integer.match(value)
                if match_integer is None:
                    print(f'Error: Parse error on sensor reading for: {name}')
                    continue
                rpmstr = match_integer.groups()[0]
                sensor.rpm = int(rpmstr)
            else:
                sensor.rpm = 0
                print(f'Error: Unable to get sensor reading for: {name}')

            if 'Normal Maximum' in sensor_data:
                value = sensor_data['Normal Maximum']
                match_integer = self.pat_integer.match(value)
                if match_integer is None:
                    print(f'Error: Parse error on sensor maximum for: {name}')
                    continue
                maxstr = match_integer.groups()[0]
                sensor.max = int(maxstr)
            else:
                sensor.max = 0
                print(f'Error: Unable to get sensor maximum for: {name}')

        self.dump_sensors(state)

    def dump_sensors(self, state: ControllerState) -> None:
        """
        Dump sensors to console.
        """
        names = state.fan_map.keys()
        for name in sorted(names):
            fan = state.fan_map[name]
            print(fan)

    def set_fan_speed(self, fan_speed: int) -> None:
        """
        Set fan speed in percent.
        """
        self.set_static_fans()
        self.ipmitool.raw(bytearray([0x30, 0x30, 0x02, 0xff, fan_speed]))

    def set_static_fans(self) -> None:
        """
        Enable static fan speed mode.
        """
        self.ipmitool.raw(bytearray([0x30, 0x30, 0x02, 0x01, 0x00]))

    def set_dynamic_fans(self) -> None:
        """
        Enable dynamic fan speed mode.
        The BMC controls fan speed dynamically, but is not very likely to use
        low fan speeds.
        """
        self.ipmitool.raw(bytearray([0x30, 0x30, 0x02, 0x01, 0x01]))
