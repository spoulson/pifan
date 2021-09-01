# PiFan
Automatic fan controller for Dell PowerEdge servers G12+.

Optimizes chassis fans to run as low as necessary to maintain safe thermals
while minimizing noise and power consumption.

Uses IPMI protocol to continually monitor CPU temperatures and adjust chassis
fan speeds accordingly.  Computes required fan speed using an easing algorithm
based on the maximum of current CPU temperatures.

# Tested Platforms
Tested on servers:

* Dell PowerEdge R720.

Tested on Raspberry Pi models:

* Raspberry Pi Desktop in VMware ESXi
* *(physical Pis to be tested soon...)*

I'd like more platforms to test.

# System Requirements
Designed to be installed and run on Raspberry Pi OS.  Though, it's possible it will work on other Linux flavors since Raspberry Pi OS is a variant of Debian.

## Pre-requisites
* `ipmitool`: CLI tool for calling IPMI requests to server's iDRAC.

```
$ sudo apt install ipmitool
```

# Install from Source
Raspberry Pi OS comes shipped with Python 3 and Pip.  This makes installation straightforward:

```sh
$ make install

or

$ sudo -H pip3 install --upgrade .
```

# Usage
```
usage: pifan [-h] [--interval SEC] [--idealtemp DEG_C] [--maxtemp DEG_C]
             [--easing TYPE] [--dry-run]
             HOST USERNAME PASSWORD

Dell PowerEdge fan speed controller for Raspberry Pi.

positional arguments:
  HOST               Target host
  USERNAME           Username
  PASSWORD           Password

optional arguments:
  -h, --help         show this help message and exit
  --interval SEC     Delay between polls
  --idealtemp DEG_C  Ideal temperature (default: 40)
  --maxtemp DEG_C    Max allowable temperature (default: 75)
  --easing TYPE      Fan speed easing type: linear | parabolic (default: parabolic)
  --dry-run          Dry run: don't change server settings
```

## Ideal Temp
Set this to the temperature to allow fans to run at 0%.  Pifan will increase
fans anywhere above this temperature.  Floating point is allowed.

Note: Fans don't actually stop at 0%.  The BMC will continue to run fans at a
minimum speed of 1200 rpm.

## Max Temp
Set this to the temperature that requires 100% fans. (VERY LOUD!)  Floating point is allowed.

# Best Practices
* Run PiFan on a physical Pi.
* Power the Pi with a UPS.

# Setup Development Environment
Most of the Python operations are wrapped in `pipenv` so as not to step all
over globally installed packages.  This is installed with `make`:

```sh
$ make tools
```

Static analysis:
```sh
$ make lint mypy pycodestyle
```

Install with "editable" option for testing and development:
```sh
$ sudo -H pip3 install -e .
```
