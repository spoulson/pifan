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

## Server Pre-requisites
* iDRAC must be enabled for IPMI.
   * For iDRAC 7, see web admin iDRAC Settings -> Network.  Tick "Enable NIC".  Configure "IPv4 Settings".  Tick "Enable IPMI Over LAN".  Click "Apply".

## Raspberry Pi Pre-requisites
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
usage: pifan [-h] [--interval SEC] [--count N] [--idealtemp DEG_C]
             [--maxtemp DEG_C] [--easing TYPE] [--sample-size N] [--dry-run]
             HOST USERNAME PASSWORD

Dell PowerEdge fan speed controller for Raspberry Pi.

positional arguments:
  HOST               Target host
  USERNAME           Username
  PASSWORD           Password

optional arguments:
  -h, --help         show this help message and exit
  --interval SEC     Delay between polls (default: 10)
  --count N          Number of polls, 0=unlimited (default: 0)
  --idealtemp DEG_C  Ideal temperature (default: 40)
  --maxtemp DEG_C    Max allowable temperature (default: 75)
  --easing TYPE      Fan speed easing type: linear | parabolic (default: parabolic)
  --sample-size N    Sample size of CPU temp average aggregation (default: 3)
  --dry-run          Dry run: don't change server settings
```

## Host
Set to hostname or IP of server's iDRAC.

## Username and Password
Use the iDRAC web admin credentials.

## Ideal Temp
Set to the temperature to allow fans to run at 0%.  Pifan will increase fans
anywhere above this temperature.  Floating point is allowed.

Note: Fans don't actually stop at 0%.  The BMC will continue to run fans at a
minimum speed of 1200 rpm.

## Max Temp
Set to the temperature that requires 100% fans. (VERY LOUD!)  Floating point is
allowed.

# Best Practices
* Run PiFan on a physical Pi.
* Deploy PiFan as a [cron job](#cron-job-deployment).
* Power the Pi with a UPS.

# Cron Job Deployment
Maintain multiple servers by deploying a cron job for each server.  Be sure to
use the `--count` option to limit polling.

Since cron typically schedules at minute intervals, it is possible to do
sub-minute polling using a combination of `--interval` and `--count` to poll
multiple times in a single cron job.

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

Install in home directory with "editable" option for testing and development:
```sh
$ pipenv install -e .
$ pipenv run pifan -h
```
