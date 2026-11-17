"""Deterministic consumption comparisons for validated invoice data."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

import numpy as np
import pandas as pd

from app.schemas.analysis import AnalysisOut

TWO_PLACES = Decimal("0.01")


def analyze(
    current: Decimal | None,
    previous: Decimal | None,
    history: Iterable[Decimal | None],
    threshold: Decimal = Decimal("30"),
) -> AnalysisOut:
    """Compare consecutive periods; history contains prior periods only."""
    valid = [value for value in history if value is not None and value >= 0]
    average = None
    median = None
    mad = None
    if valid:
        series = pd.Series([float(value) for value in valid], dtype="float64")
        average = (sum(valid) / Decimal(len(valid))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        if len(series) >= 4:
            median_float = float(np.median(series.to_numpy()))
            median = Decimal(str(median_float)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            mad_float = float(np.median(np.abs(series.to_numpy() - median_float)))
            mad = Decimal(str(mad_float)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    if current is None or previous is None or previous == 0:
        return AnalysisOut(
            current_consumption_m3=current,
            previous_consumption_m3=previous,
            historical_average_m3=average,
            historical_median_m3=median,
            historical_mad_m3=mad,
            status="insufficient_data",
            message="No hay datos suficientes para calcular la variación frente al período anterior.",
        )

    variation = ((current - previous) / previous * 100).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    if variation > threshold:
        status = "high_variation"
        message = f"El consumo aumentó un {str(variation).replace('.', ',')} % respecto al período anterior."
    elif variation < -threshold:
        status = "significant_decrease"
        message = f"El consumo disminuyó un {str(abs(variation)).replace('.', ',')} % respecto al período anterior."
    else:
        status = "within_threshold"
        message = "La variación del consumo está dentro del umbral de demostración configurado."

    return AnalysisOut(
        current_consumption_m3=current,
        previous_consumption_m3=previous,
        variation_percentage=variation,
        historical_average_m3=average,
        historical_median_m3=median,
        historical_mad_m3=mad,
        status=status,
        message=message,
    )
