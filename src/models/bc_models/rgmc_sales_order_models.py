"""RGMC custom API — Sales Order Pydantic models (Pag50216 / Pag50217)."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RgmcSalesOrderCreate(BaseModel):
    sellToCustomerNo: Optional[str] = None
    sellToContactNo: Optional[str] = None
    externalDocumentNo: Optional[str] = None
    postingDate: Optional[str] = None
    orderDate: Optional[str] = None
    documentDate: Optional[str] = None
    requestedDeliveryDate: Optional[str] = None
    locationCode: Optional[str] = None
    salespersonCode: Optional[str] = None
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None
    submittedBy: Optional[str] = None
    lines: Optional[List[Dict[str, Any]]] = None


class RgmcSalesOrderUpdate(BaseModel):
    sellToCustomerNo: Optional[str] = None
    sellToContactNo: Optional[str] = None
    externalDocumentNo: Optional[str] = None
    postingDate: Optional[str] = None
    orderDate: Optional[str] = None
    documentDate: Optional[str] = None
    requestedDeliveryDate: Optional[str] = None
    locationCode: Optional[str] = None
    salespersonCode: Optional[str] = None
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None
    submittedBy: Optional[str] = None


class RgmcSalesOrderLineCreate(BaseModel):
    lineType: Optional[str] = None
    number: Optional[str] = None
    description: Optional[str] = None
    description2: Optional[str] = None
    unitOfMeasureCode: Optional[str] = None
    quantity: Optional[float] = None
    unitPrice: Optional[float] = None
    lineDiscountPercent: Optional[float] = None
    lineAmount: Optional[float] = None
    shipmentDate: Optional[str] = None
    locationCode: Optional[str] = None
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None


class RgmcSalesOrderLineUpdate(RgmcSalesOrderLineCreate):
    pass
