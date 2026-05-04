from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemGroup(BaseModel):
    itemGroupId: int
    itemGroupCode: Optional[str] = ""
    name: Optional[str] = ""
    remark: Optional[str] = ""
    isRW: Optional[bool] = False
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class Category(BaseModel):
    categoryId: int
    categoryCode: Optional[str] = ""
    name: Optional[str] = ""
    brandId: Optional[int] = None
    itemGroupId: Optional[int] = None
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class CategoryLookUpSM(BaseModel):
    categoryId: int
    categoryName: Optional[str] = ""
    itemGroupName: Optional[str] = ""
    brandId: Optional[int] = None
    subClassCode: Optional[str] = ""
