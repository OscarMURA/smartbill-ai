from decimal import Decimal

from app.services.consumption_analyzer import analyze


def test_demo_increase() -> None:
    result = analyze(Decimal("32"), Decimal("22"), [Decimal(x) for x in (19, 21, 20, 23, 22)])
    assert result.variation_percentage == Decimal("45.45")
    assert result.status == "high_variation"
    assert result.historical_median_m3 == Decimal("21.00")


def test_zero_previous_is_insufficient() -> None:
    result = analyze(Decimal("32"), Decimal("0"), [Decimal("0")])
    assert result.variation_percentage is None
    assert result.status == "insufficient_data"


def test_threshold_boundaries() -> None:
    assert analyze(Decimal("13"), Decimal("10"), []).status == "within_threshold"
    assert analyze(Decimal("7"), Decimal("10"), []).status == "within_threshold"
    assert analyze(Decimal("6"), Decimal("10"), []).status == "significant_decrease"
