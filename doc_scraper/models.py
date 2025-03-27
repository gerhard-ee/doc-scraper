from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MenuNode:
    url: str
    title: str
    children: List["MenuNode"]
    level: int
    parent_url: Optional[str] = None
