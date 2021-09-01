"""
Wrapper for ipmitool command.
https://docs.oracle.com/cd/E19464-01/820-6850-11/IPMItool.html
"""

import re
import subprocess
import sys
from typing import Dict, List
from .util import parse_pdv


class Ipmitool:
    """
    Wrapper for ipmitool CLI tool.
    https://docs.oracle.com/cd/E19464-01/820-6850-11/IPMItool.html#50602039_68835
    """
    cmd_base: List[str]

    cmd_base_print: List[str]

    def __init__(self, host: str, username: str, password: str) -> None:
        cmd_start = [
            'ipmitool',
            '-I', 'lanplus',
            '-H', host,
            '-U', username
        ]
        self.cmd_base = cmd_start + ['-P', password]
        self.cmd_base_print = cmd_start + ['-P', '*']

    def _run(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = self.cmd_base + args
        print(' '.join(self.cmd_base_print + args))
        try:
            return subprocess.run(cmd, capture_output=True, encoding='utf-8')
        except KeyboardInterrupt:
            sys.exit()

    def sdr_type(self, sensor_type: str) -> List[List[str]]:
        """
        Call `ipmitool sdr type`.
        Output format::

            <name> | <sensor id hex>h | <ok_status> |
            <entity_id>.<instance_id> | <status>

        """
        response = self._run(['sdr', 'type', sensor_type])
        if response.returncode != 0:
            print(response.stderr)
            raise Exception('Error in ipmitool.sdr_type()')

        return parse_pdv(response.stdout)

    def sdr_get(self, sensor_names: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Call `ipmitool sdr get`.
        Output format::

            Sensor ID: <name> (<id_hex>)
             <field>: <value>
             ...

        """
        response = self._run(['sdr', 'get'] + sensor_names)
        if response.returncode != 0:
            print(response.stderr)
            raise Exception('Error in ipmitool.sdr_get()')

        result: Dict[str, Dict[str, str]] = {}
        header_re = re.compile(r'^\S.+:(.+)')
        prop_re = re.compile(r'^ (.+):(.*)')
        name: str = ''
        item: Dict[str, str] = {}

        for line in response.stdout.split('\n'):
            match_header = header_re.match(line)
            if match_header is not None:
                name = match_header.groups()[0].strip()
                item = {}
                result[name] = item
                continue

            match_prop = prop_re.match(line)
            if match_prop is not None:
                key = match_prop.groups()[0].strip()
                value = match_prop.groups()[1].strip()
                item[key] = value
                result[name] = item
                continue

        return result

    def raw(self, raw_data: bytearray) -> None:
        """
        Call `ipmitool raw`.
        """
        payload = [('0x' + format(value, '02x')) for value in raw_data]
        response = self._run(['raw'] + payload)
        if response.returncode != 0:
            print(response.stderr)
            raise Exception('Error in ipmitool.raw()')
