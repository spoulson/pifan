"""
Wrapper for ipmitool command.
"""

import re
import subprocess
from typing import Dict, List
from .util import parse_pdv

class Ipmitool:
    cmd_base: List[str]

    cmd_base_print: List[str]

    def __init__(self, host: str, username: str, password: str) -> None:
        self.fans = {}
        cmd_start = [
                'ipmitool',
                '-I', 'lanplus',
                '-H', host,
                '-U' ,username,
        ]
        self.cmd_base = cmd_start + ['-P', password]
        self.cmd_base_print = cmd_start + ['-P', '*']

    def _run(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = self.cmd_base + args
        print(' '.join(self.cmd_base_print + args))
        return subprocess.run(cmd, capture_output=True, encoding='utf-8')

    def sdr_type(self, type: str) -> List[List[str]]:
        response = self._run(['sdr', 'type', type])
        if response.returncode != 0:
            print(response.stderr)
            raise Exception('Error in ipmitool.sdr_type()')

        return parse_pdv(response.stdout)

    def sdr_get(self, sensor_names: List[str]) -> Dict[str, List[str]]:
        response = self._run(['sdr', 'get'] + sensor_names)
        if response.returncode != 0:
            print(response.stderr)
            raise Exception('Error in ipmitool.sdr_get()')

        result: Dict[str, List[str]] = {}
        header_re = re.compile('^\S.+:(.+)')
        prop_re = re.compile('^ (.+):(.*)')
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
        Send a raw data request.
        """
        response = self._run(['raw'] + [('0x' + format(value, '02x')) for value in raw_data])
        if response.returncode != 0:
            print(response.stderr)
            raise Exception('Error in ipmitool.raw()')
