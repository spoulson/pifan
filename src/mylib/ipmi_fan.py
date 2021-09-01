"""
IPMI control of chassis fans.
"""

import re
from typing import Dict
from .ipmitool import Ipmitool
from .util import parse_hex, parse_pdv

class FanSensor:
    name: str

    id: int

    rpm: int

    max: int

    def __init__(self) -> None:
        self.name = ''
        self.id = 0
        self.rpm = 0
        self.max = 0

    def __str__(self) -> str:
        return f'FanSensor: name={self.name}, id={self.id:#x}, rpm={self.rpm}, max={self.max}, percent={self.percent():.1f}%'

    def percent(self) -> float:
        if self.max == 0:
            return float('nan')

        return float(self.rpm) / float(self.max) * 100.0

class IpmiFan:
    fan_map: Dict[str, FanSensor]

    ipmitool: Ipmitool

    pat_fan = re.compile('^Fan\d+$')
    pat_name = re.compile('^(.+) \(')
    pat_integer = re.compile('^(\d+)')

    def __init__(self, host: str, username: str, password: str) -> None:
        self.fans = {}
        self.ipmitool = Ipmitool(host, username, password)

    def discover_sensors(self) -> None:
        """
        Query IPMI for list of chassis fans.
        Must call this method first before using this class.
        """
        # https://docs.oracle.com/cd/E19464-01/820-6850-11/IPMItool.html#50602039_68835
        # Enumerate fans:
        # ipmitool ... sdr type fan
        # Enumerate thermals:
        # ipmitool ... sdr type temperature
        # Output format: <name> | <sensor id hex>h | <ok_status> | <entity_id>.<instance_id> | <status>
        #
        # Get single sensor reading:
        # ipmitool ... sensor reading <name1> <name2> ...
        # Output format: <name> | <status>
        #
        # Get sensor details:
        # ipmitool ... sensor get <name1> <name2> ...
        # Output format:
        #   Sensor ID: <name> (<id_hex>)
        #    <field>: <value>
        #    ...

        # enum_fans_cmd = self.cmd_base + ['sdr', 'type', 'fan']
        # response = subprocess.run(enum_fans_cmd, capture_output=True, encoding='utf-8')
        # if response.returncode != 0:
        #     raise Exception('Error in ipmitool while enumerating fans')

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

        self.fan_map = fan_map

        # Read sensor values.
        self.read_sensors()

    def read_sensors(self) -> None:
        """
        Read current sensor values.
        Store values in self.fan_map.
        """
        fan_names = list(self.fan_map.keys())
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

        for key in result.keys():
            # Sensor name.
            match_name = self.pat_name.match(key)
            if match_name is None:
                continue

            name = match_name.groups()[0]
            sensor_data = result[key]
            sensor = self.fan_map[name]

            if 'Sensor Reading' in sensor_data:
                match_integer = self.pat_integer.match(sensor_data['Sensor Reading'])
                if match_integer is None:
                    print(f'Error: Parse error on sensor reading for: {name}')
                    continue
                rpmstr = match_integer.groups()[0]
                sensor.rpm = int(rpmstr)
            else:
                sensor.rpm = 0
                print(f'Error: Unable to get sensor reading for: {name}')

            if 'Normal Maximum' in sensor_data:
                match_integer = self.pat_integer.match(sensor_data['Normal Maximum'])
                if match_integer is None:
                    print(f'Error: Parse error on sensor maximum for: {name}')
                    continue
                maxstr = match_integer.groups()[0]
                sensor.max = int(maxstr)
            else:
                sensor.max = 0
                print(f'Error: Unable to get sensor maximum for: {name}')

        self.dump_sensors()

    def dump_sensors(self) -> None:
        """
        Dump sensors to console.
        """
        names = self.fan_map.keys()
        for name in sorted(names):
            fan = self.fan_map[name]
            print(fan)

    def set_fan_speed(self, fan_speed: int) -> None:
        """
        Set fan speed in percent.
        """
        self.set_static_fans()
        # raw 0x30 0x30 0x02 0xff <percent hex>
        self.ipmitool.raw(bytearray([0x30, 0x30, 0x02, 0xff, fan_speed]))

    def set_static_fans(self) -> None:
        # raw 0x30 0x30 0x01 0x00
        self.ipmitool.raw(bytearray([0x30, 0x30, 0x02, 0x01, 0x00]))

    def set_dynamic_fans(self) -> None:
        # raw 0x30 0x30 0x01 0x01
        self.ipmitool.raw(bytearray([0x30, 0x30, 0x02, 0x01, 0x01]))
