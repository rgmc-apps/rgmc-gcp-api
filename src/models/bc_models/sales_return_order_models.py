"""RGMC custom API — Sales Return Order Pydantic models (Pag50201 / Pag50202)."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SalesReturnOrderCreate(BaseModel):
    customerNumber: Optional[str] = None
    externalDocumentNo: Optional[str] = None
    sellToCustomerNo: Optional[str] = None
    lines: Optional[List[Dict[str, Any]]] = None
    sellToContactNo: Optional[str] = None
    sellToAddress: Optional[str] = None
    sellToAddress2: Optional[str] = None
    sellToPostCode: Optional[str] = None
    sellToCity: Optional[str] = None
    billToCustomerNo: Optional[str] = None
    billToContactNo: Optional[str] = None
    billToAddress: Optional[str] = None
    billToAddress2: Optional[str] = None
    billToPostCode: Optional[str] = None
    billToCity: Optional[str] = None
    billToCountryRegionCode: Optional[str] = None
    shipToCode: Optional[str] = None
    shipToName: Optional[str] = None
    shipToAddress: Optional[str] = None
    shipToAddress2: Optional[str] = None
    shipToPostCode: Optional[str] = None
    shipToCity: Optional[str] = None
    shipToCountryRegionCode: Optional[str] = None
    shipToContact: Optional[str] = None
    postingDate: Optional[str] = None
    orderDate: Optional[str] = None
    documentDate: Optional[str] = None
    shipmentDate: Optional[str] = None
    pricesIncludingVat: Optional[bool] = None
    vatBusPostingGroup: Optional[str] = None
    locationCode: Optional[str] = None
    salespersonCode: Optional[str] = None
    campaignNo: Optional[str] = None
    responsibilityCenter: Optional[str] = None
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None


class SalesReturnOrderUpdate(SalesReturnOrderCreate):
    pass


class SalesReturnOrderLineCreate(BaseModel):
    lineType: Optional[str] = None
    number: Optional[str] = None
    description: Optional[str] = None
    description2: Optional[str] = None
    unitOfMeasureCode: Optional[str] = None
    quantity: Optional[float] = None
    returnQtyToReceive: Optional[float] = None
    qtyToInvoice: Optional[float] = None
    unitPrice: Optional[float] = None
    lineDiscountPercent: Optional[float] = None
    lineAmount: Optional[float] = None
    returnReasonCode: Optional[str] = None
    locationCode: Optional[str] = None
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None


class SalesReturnOrderLineUpdate(SalesReturnOrderLineCreate):
    pass
