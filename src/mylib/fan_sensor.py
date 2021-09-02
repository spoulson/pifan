"""
Fan sensor state.
"""


class FanSensor:
    """
    Fan sensor state.
    """
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
        return(f'FanSensor: name={self.name}, id={self.id:#x}, '
               f'rpm={self.rpm}, max={self.max}, '
               f'percent={self.percent():0.1f}%')

    def percent(self) -> float:
        """
        Compute fan percentage.
        """
        if self.max == 0:
            return float('nan')

        return float(self.rpm) / float(self.max) * 100.0
