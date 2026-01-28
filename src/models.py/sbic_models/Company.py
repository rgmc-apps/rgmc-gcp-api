from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Company(BaseModel):
    companyid: int 
    companycode: Optional[str] = ""
    name: Optional[str] = ""
    initials: Optional[str] = ""
    address: Optional[str] = ""
    businessstyle: Optional[str] = ""
    tin: Optional[str] = ""
    remark: Optional[str] = ""
    isactive: bool = True
    createby: Optional[int] = -1
    createdate: datetime = datetime.now
    updateby: Optional[int] = -1
    updatedate: datetime = datetime.now