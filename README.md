# Pi Fan

Automatic fan controller for Dell PowerEdge servers G12+.

Monitor CPU temperatures and adjust chassis fans accordingly.  Computes required fan speed using an easing formula based on the maximum CPU temperature.

# Tested Platforms
Tested on Dell PowerEdge R720.

# Install from Source

```sh
make install
```

# Usage
```
usage: pifan [-h] [--idealtemp DEG_C] [--maxtemp DEG_C] [--easing TYPE]
             HOST USERNAME PASSWORD

Dell PowerEdge fan speed controller for Raspberry Pi.

positional arguments:
  HOST               Target host
  USERNAME           Username
  PASSWORD           Password

optional arguments:
  -h, --help         show this help message and exit
  --idealtemp DEG_C  Ideal temperature (default: 40)
  --maxtemp DEG_C    Max allowable temperature (default: 75)
  --easing TYPE      Fan speed easing type: linear | parabolic (default: parabolic)
```

## Ideal Temp
Set this to the temperature where you can afford to shut off the fans.  Pifan will increase fans anywhere above this temperature.  Floating point is allowed.

## Max Temp
Set this to the temperature that requires 100% fans. (VERY LOUD!)  Floating point is allowed.
