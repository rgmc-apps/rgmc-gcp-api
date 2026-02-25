from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CustomerPOUL(BaseModel):
    companyId: int
    companyName: Optional[str] = ""
    warehouseId: Optional[int] = None
    customerId: Optional[int] = None
    customerName: Optional[str] = ""
    poRefNumber: Optional[str] = ""
    poDate: Optional[datetime] = None
    deliveryDate: Optional[datetime] = None
    cancellationDate: Optional[datetime] = None
    customerBranchId: Optional[int] = None
    customerBranchName: Optional[str] = ""
    customerBranchLookUpCode: Optional[str] = ""
    remark: Optional[str] = ""
    customerPOId: Optional[int] = None
    poStatus: Optional[str] = ""
    manualEncoded: Optional[bool] = False
    createBy: Optional[int] = None
    createDate: Optional[datetime] = None
    updateBy: Optional[int] = None
    updateDate: Optional[datetime] = None
    cancelBy: Optional[int] = None
    cancelDate: Optional[datetime] = None
    cancelReason: Optional[str] = ""
