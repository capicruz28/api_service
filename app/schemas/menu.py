from pydantic import BaseModel, Field
from typing import List, Optional

class MenuItem(BaseModel):
    id: int = Field(..., alias='MenuId')
    name: str = Field(..., alias='Name')
    icon: str = Field(..., alias='Icon')
    path: str = Field(..., alias='Path')
    order_index: int = Field(..., alias='OrderIndex')
    level: int = Field(..., alias='Level')
    parent_id: Optional[int] = Field(None, alias='ParentId')
    children: List['MenuItem'] = []

    class Config:
        from_attributes = True
        populate_by_name = True

class MenuResponse(BaseModel):
    data: List[MenuItem]
    message: str = "Success"