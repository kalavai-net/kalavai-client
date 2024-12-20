"""
Hack: Fix for pydantic issue with petals ModelInfo

Copy this over health.petals.dev/data_structures.py
"""
from typing import Annotated, Optional
from urllib.parse import urlparse
import dataclasses

import pydantic


@pydantic.dataclasses.dataclass
class ModelInfo():
    num_blocks: Annotated[int, pydantic.Field(strict=True, ge=1)]
    repository: Optional[str] = None
    dht_prefix: Optional[str] = None
    official: bool = True
    limited: bool = False
    

    @property
    def name(self) -> str:
        return urlparse(self.repository).path.lstrip("/")

    @property
    def short_name(self) -> str:
        return self.name.split("/")[-1]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, source: dict):
        return cls(**source)
