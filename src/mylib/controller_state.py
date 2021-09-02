"""
Runtime state of PiFanController.
"""
from datetime import datetime, timedelta
from functools import reduce
import pickle
from typing import Dict, List
from .cpu_sensor import CpuSensor
from .fan_sensor import FanSensor


class ControllerState:
    """
    Runtime state of PiFanController.
    """
    sample_size: int

    samples: List[float]

    cpu_map: Dict[str, CpuSensor]

    fan_map: Dict[str, FanSensor]

    # Epoch seconds.
    last_sample_time: float

    def __init__(self):
        self.sample_size = 3
        self.samples = []
        self.last_sample_time = None
        self.cpu_map = None
        self.fan_map = None

    def add_aggregate_temp(self, value: float) -> float:
        """
        Add a CPU temp value to aggregate average.
        Return new average.
        """
        # Check if aggregate samples are too old.
        if self.last_sample_time is not None:
            last_sample_time2 = datetime.fromtimestamp(self.last_sample_time)
            now = datetime.now()
            threshold_time = now - timedelta(hours=1)
            if last_sample_time2 < threshold_time:
                # Too old, clear samples.
                self.samples = []

        self.samples.append(value)
        self.samples = self.samples[-self.sample_size:]
        agg_value = reduce(
            lambda a, b: a + b,
            self.samples
        ) / len(self.samples)
        self.last_sample_time = datetime.now().timestamp()
        return agg_value

    def set_sample_size(self, sample_size: int) -> None:
        """
        Set sample size.
        """
        self.sample_size = sample_size
        self.samples = self.samples[-sample_size:]

    def restore(self, serialized: bytes) -> None:
        """
        Restore state from serialized data previously created by dump().
        """
        loaded_state = pickle.loads(serialized)
        self.__dict__.update(loaded_state.__dict__)

    def dump(self) -> bytes:
        """
        Serialize state.
        """
        return pickle.dumps(self)
