from typing import List, Optional
from pydantic import BaseModel

class MenuItem(BaseModel): 
    id: int
    name: str
    icon: str
    path: str
    order_index: int
    level: int
    children: List['MenuItem'] = [] 

    class Config:
        from_attributes = True

class MenuResponse(BaseModel):
    menu: List[MenuItem]
    status: str = "success"