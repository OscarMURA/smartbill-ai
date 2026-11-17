from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class LineItem(BaseModel):
    label: str
    amount_cop: int


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collection_id: UUID
    billing_period: str | None = None
    issued_on: date | None = None
    due_on: date | None = None
    consumption_m3: Decimal | None = None
    total_cop: int | None = None
    fixed_charge_cop: int | None = None
    variable_charge_cop: int | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source: Literal["synthetic", "local_upload"]

    @field_serializer("consumption_m3", when_used="json")
    def serialize_consumption(self, value: Decimal | None) -> int | float | None:
        if value is None:
            return None
        return int(value) if value == value.to_integral_value() else float(value)
