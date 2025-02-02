from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Car:
    """Represents a car entity in the domain."""
    title: str
    price: float
    mileage: int
    year: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert the car instance to a dictionary."""
        return asdict(self)
