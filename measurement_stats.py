from math import sqrt


class MeasurementSeries:
    """Накопительная статистика одной серии измерений."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0
        self.mean = 0.0
        self._sum_squared_deviations = 0.0

    def add(self, value: float):
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self._sum_squared_deviations += delta * (value - self.mean)

    @property
    def standard_deviation(self):
        if self.count < 2:
            return None

        variance = self._sum_squared_deviations / (self.count - 1)
        return sqrt(variance)


class MeasurementRun:
    """Статистика всех величин за один сеанс измерения."""

    QUANTITIES = (
        "voltage",
        "current",
        "power",
    )
    MIN_SAMPLES = 10

    def __init__(self, device_type):
        if device_type not in ("single", "dual"):
            raise ValueError(f"Unknown device type: {device_type}")

        self.device_type = device_type
        self.channels = ("ch1",) if device_type == "single" else ("ch1", "ch2")
        self.count = 0
        self.series = {
            (channel, quantity): MeasurementSeries()
            for channel in self.channels
            for quantity in self.QUANTITIES
        }

    def add_reading(self, params):
        """Добавляет показания одного успешного цикла опроса."""
        readings = {"ch1": params} if self.device_type == "single" else params

        values = {
            (channel, quantity): readings[channel][quantity]
            for channel, quantity in self.series
        }
        for key, value in values.items():
            self.series[key].add(value)

        self.count += 1

    @property
    def ready(self):
        return self.count >= self.MIN_SAMPLES