"""Trade Portal Brand Model."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Brand(BaseModel):
    brandid: Optional[int] = Field(default=None, primary_key=True)
    brandcode: str = ""
    name: Optional[str] = ""
    companyid: Optional[int] = None
    initials: str = ""
    remark: str = ""
    isactive: Optional[bool] = True
    createby: Optional[str] = ""
    createdate: datetime
    updateby: Optional[str] = ""
    updatedate: Optional[datetime] = Field(default_factory=datetime.now)