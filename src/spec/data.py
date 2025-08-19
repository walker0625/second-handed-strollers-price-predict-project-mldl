from dataclasses import dataclass

@dataclass
class Item:
    title: str
    detail: str
    condition: str
    uploaded_date: str
    is_completed: bool
    price: int
