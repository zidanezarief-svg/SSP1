from decimal import Decimal
from pydantic import BaseModel, Field

class OrderItemRequest(BaseModel):
    menu_item_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

class OrderRequest(BaseModel):
    customer_name: str = Field(
        default="Walk-in Customer",
        min_length=1,
        max_length=100
    )
    items: list[OrderItemRequest] = Field(min_length=1)

class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)
    patty_count: int = Field(default=1, gt=0)
    category_id: int | None = Field(default=None, gt=0)

class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, gt=0)
    patty_count: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)

class StockUpdate(BaseModel):
    stock_quantity: int = Field(ge=0)

class MenuCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class MenuCategoryUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )
