from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ColorGroup(BaseModel):
    colorGroupId: int
    colorGroupCode: Optional[str] = ""
    name: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class Color(BaseModel):
    colorId: int
    colorCode: Optional[str] = ""
    name: Optional[str] = ""
    colorGroupId: Optional[int] = None
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class SMColor(BaseModel):
    smColorCode: str
    lookUpCode: Optional[str] = ""
    remark: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    tmpColorId: Optional[int] = None
