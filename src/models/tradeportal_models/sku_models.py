from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class KCCSKU(BaseModel):
    brandId: int
    stockNumber: Optional[str] = ""
    skuDesc: Optional[str] = ""
    seasonDate: Optional[date] = None
    seasonCode: Optional[str] = ""
    unitPrice: Optional[float] = 0.0
    skuCode: Optional[str] = ""
    barcode: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    vendorBarcode: Optional[str] = ""
    isMarkdown: Optional[bool] = False
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class LMSKU(BaseModel):
    brandId: int
    skuCode: Optional[str] = ""
    barcode: Optional[str] = ""
    skuDesc: Optional[str] = ""
    unitPrice: Optional[float] = 0.0
    oldPrice: Optional[float] = 0.0
    vendorCode: Optional[str] = ""
    subDeptCode: Optional[str] = ""
    stockNumber: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    vendorBarcode: Optional[str] = ""
    isMarkdown: Optional[bool] = False
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class MGSKU(BaseModel):
    brandId: int
    barcode: Optional[str] = ""
    deptCode: Optional[str] = ""
    skuDesc: Optional[str] = ""
    unitPrice: Optional[float] = 0.0
    vendorCode: Optional[str] = ""
    seasonCode: Optional[str] = ""
    stockNumber: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    vendorBarcode: Optional[str] = ""
    isMarkdown: Optional[bool] = False
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class RDSSKU(BaseModel):
    customerSiteId: int
    brandId: int
    vendorCode: Optional[str] = ""
    vendorPartNo: Optional[str] = ""
    subDeptCode: Optional[str] = ""
    skuDesc: Optional[str] = ""
    skuCode: Optional[str] = ""
    barcode: Optional[str] = ""
    initial: Optional[str] = ""
    unitPrice: Optional[float] = 0.0
    oldPrice: Optional[float] = 0.0
    stockNumber: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    vendorBarcode: Optional[str] = ""
    skuStyle: Optional[str] = ""
    isMarkdown: Optional[bool] = False
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class RDSSaleSKU(BaseModel):
    customerSiteId: int
    brandId: int
    vendorCode: Optional[str] = ""
    vendorPartNo: Optional[str] = ""
    subDeptCode: Optional[str] = ""
    skuDesc: Optional[str] = ""
    skuCode: Optional[str] = ""
    barcode: Optional[str] = ""
    initial: Optional[str] = ""
    unitPrice: Optional[float] = 0.0
    oldPrice: Optional[float] = 0.0
    stockNumber: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class SMSKU(BaseModel):
    vendorCode: Optional[str] = ""
    deptCode: Optional[str] = ""
    subDeptCode: Optional[str] = ""
    classCode: Optional[str] = ""
    subClassCode: Optional[str] = ""
    smStockDesc: Optional[str] = ""
    unitRetailAmount: Optional[float] = 0.0
    vendorUpcCode: Optional[str] = ""
    smUpcCode: Optional[str] = ""
    smStockCode: str
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    siteId: Optional[int] = None


class SMSKURequest(BaseModel):
    itemNo: int
    vendorCode: Optional[str] = ""
    deptCode: Optional[str] = ""
    subDeptCode: Optional[str] = ""
    classCode: Optional[str] = ""
    subClassCode: Optional[str] = ""
    brandCode: Optional[str] = ""
    description: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    vendorPartStockNo: Optional[str] = ""
    barcode: Optional[str] = ""
    retailAmount: Optional[float] = 0.0
    marginCode: Optional[str] = ""
    tagCode: Optional[str] = ""
    backUpdate: Optional[date] = None
    sysDate: Optional[date] = None
    smStockDesc: Optional[str] = ""
    smStockCode: Optional[str] = ""
    saleItem: Optional[bool] = False
    status: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None
    siteId: Optional[int] = None
    vendorBarcode: Optional[str] = ""
    oldBarcode: Optional[str] = ""
    oldSMStockCode: Optional[str] = ""


class SMProduct(BaseModel):
    barCode: str
    stockNo: Optional[str] = ""
    category: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    description: Optional[str] = ""
    season: Optional[date] = None
    srp: Optional[float] = 0.0
