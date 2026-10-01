"""Input fields are excluded from representations and never echoed in errors."""

from pydantic import BaseModel, ConfigDict, Field


class ScanInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)
    content: str = Field(min_length=1, max_length=1_048_576, repr=False)
    filename: str = Field(default="submitted.txt", min_length=1, max_length=255, repr=False)
