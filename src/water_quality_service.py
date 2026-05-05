# src/water_quality_service.py


class Result:
    def __init__(self, status: str, alert: bool):
        self.status = status
        self.alert = alert


class WaterQualityService:
    def __init__(self, warning_threshold: float, critical_threshold: float):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def evaluate_turbidity(self, value: float) -> Result:
        if value > self.critical_threshold:
            return Result(status="CRITICAL", alert=True)
        return Result(status="NORMAL", alert=False)
