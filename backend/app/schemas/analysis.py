from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_serializer


class AnalysisOut(BaseModel):
    current_consumption_m3: Decimal | None = None
    previous_consumption_m3: Decimal | None = None
    variation_percentage: Decimal | None = None
    historical_average_m3: Decimal | None = None
    historical_median_m3: Decimal | None = None
    historical_mad_m3: Decimal | None = None
    status: Literal[
        "high_variation", "significant_decrease", "within_threshold", "insufficient_data"
    ]
    message: str

    @field_serializer(
        "current_consumption_m3", "previous_consumption_m3", "variation_percentage", "historical_average_m3",
        "historical_median_m3", "historical_mad_m3",
        when_used="json",
    )
    def serialize_decimal(self, value: Decimal | None) -> int | float | None:
        if value is None:
            return None
        return int(value) if value == value.to_integral_value() else float(value)
