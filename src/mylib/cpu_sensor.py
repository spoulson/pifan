"""
CPU sensor state.
"""


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
