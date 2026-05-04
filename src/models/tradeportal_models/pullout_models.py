from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class StockPullOut(BaseModel):
    stockPullOutId: int
    pullOutDate: Optional[date] = None
    pullOutType: Optional[str] = ""
    pullOutNumber: Optional[str] = ""
    customerId: Optional[int] = None
    sourceRefNumber: Optional[str] = ""
    sourceBrandId: Optional[int] = None
    sourceStoreId: Optional[int] = None
    sourceSiteId: Optional[int] = None
    destnBrandId: Optional[int] = None
    destnStoreId: Optional[int] = None
    destnSiteId: Optional[int] = None
    filePath: Optional[str] = ""
    downloadBy: Optional[str] = ""
    downloadDate: Optional[datetime] = None
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class StockPullOutDetail(BaseModel):
    stockPullOutId: int
    pullOutNumber: Optional[str] = ""
    destnBrandId: Optional[int] = None
    destnStoreId: Optional[int] = None
    destnSiteId: Optional[int] = None
    productId: Optional[int] = None
    price: Optional[float] = 0.0
    pullOutQty: Optional[int] = None
    isMarkdown: Optional[bool] = False
    remark: Optional[str] = ""


class StockPullOutRequest(BaseModel):
    brandId: int
    storeId: int
    pullOutDate: Optional[date] = None
    refNumber: Optional[str] = ""
    barcode: Optional[str] = ""
    pullOutQty: Optional[int] = None
    requestStatus: Optional[str] = ""
    stockPullOutId: Optional[int] = None
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class SMPullOut(BaseModel):
    siteId: int
    smPullOutId: int
    smStoreCode: Optional[str] = ""
    scpoaNumber: Optional[str] = ""
    pullOutDate: Optional[date] = None
    pullOutNumber: Optional[str] = ""
    sourceBrandId: Optional[int] = None
    sourceStoreId: Optional[int] = None
    sourceSiteId: Optional[int] = None
    destnBrandId: Optional[int] = None
    destnStoreId: Optional[int] = None
    destnSiteId: Optional[int] = None
    filePath: Optional[str] = ""
    downloadBy: Optional[str] = ""
    downloadDate: Optional[datetime] = None
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None
    oldSMStoreCode: Optional[str] = ""


class SMPullOutDetail(BaseModel):
    siteId: int
    smPullOutId: int
    destnBrandId: Optional[int] = None
    destnStoreId: Optional[int] = None
    destnSiteId: Optional[int] = None
    stockNo: Optional[str] = ""
    description: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    price: Optional[float] = 0.0
    quantity: Optional[int] = None
    smStockCode: Optional[str] = ""
    saleItem: Optional[bool] = False
    remark: Optional[str] = ""
