"""Trade Portal category Model."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Category(BaseModel):
    categoryid: int = Field(default=-1, primary_key=True)
    categorycode: str = ""
    name: str = ""
    brand_id: int = -1
    itemgroupid: int = -1
    remark: str = ""
    isactive: bool = True
    createby: str = ""
    createdate: datetime = Field(default_factory=datetime.now)
    updateby: str = ""
    updatedate: datetime = Field(default_factory=datetime.now)
