from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


def order_uid() -> str:
    alphabet = string.ascii_uppercase + string.digits  # b36
    return "O_" + "".join(secrets.choice(alphabet) for _ in range(6))


class OrderedCombo(BaseModel):
    type: Literal["combo_meal"] = "combo_meal"
    order_id: str = Field(default_factory=order_uid)
    meal_id: str
    drink_id: str
    drink_size: Literal["M", "L"] | None
    fries_size: Literal["M", "L"]
    sauce_id: str | None = None


class OrderedHappy(BaseModel):
    type: Literal["happy_meal"] = "happy_meal"
    order_id: str = Field(default_factory=order_uid)
    meal_id: str
    drink_id: str
    drink_size: Literal["S", "M", "L"] | None
    sauce_id: str | None = None


class OrderedRegular(BaseModel):
    type: Literal["regular"] = "regular"
    order_id: str = Field(default_factory=order_uid)
    item_id: str
    size: Literal["S", "M", "L"] | None = None


OrderedItem = Annotated[
    Union[OrderedCombo, OrderedHappy, OrderedRegular], Field(discriminator="type")
]


@dataclass
class OrderStateItem:
    ordered_item: OrderedItem
    name: str
    price: float
    details: dict[str, str] = field(default_factory=dict)


@dataclass
class OrderState:
    items: dict[str, OrderedItem]
    item_details: dict[str, OrderStateItem] = field(default_factory=dict)

    async def add(self, item: OrderedItem, name: str = "", price: float = 0.0, details: dict[str, str] | None = None) -> None:
        self.items[item.order_id] = item
        self.item_details[item.order_id] = OrderStateItem(
            ordered_item=item,
            name=name,
            price=price,
            details=details or {}
        )

    async def remove(self, order_id: str) -> OrderedItem:
        self.item_details.pop(order_id, None)
        return self.items.pop(order_id)

    def get(self, order_id: str) -> OrderedItem | None:
        return self.items.get(order_id)
    
    def get_formatted_order(self) -> list[dict]:
        formatted_items = []
        for order_id, state_item in self.item_details.items():
            item = state_item.ordered_item
            formatted_item = {
                "order_id": order_id,
                "type": item.type,
                "name": state_item.name,
                "price": state_item.price,
                "details": state_item.details
            }
            
            if item.type == "combo_meal":
                formatted_item["meal_id"] = item.meal_id
                formatted_item["drink_size"] = item.drink_size
                formatted_item["fries_size"] = item.fries_size
            elif item.type == "happy_meal":
                formatted_item["meal_id"] = item.meal_id
                formatted_item["drink_size"] = item.drink_size
            elif item.type == "regular":
                formatted_item["item_id"] = item.item_id
                formatted_item["size"] = item.size
                
            formatted_items.append(formatted_item)
            
        return formatted_items
