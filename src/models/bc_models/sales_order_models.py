"""Business Central Sales Order Pydantic models."""
from typing import Any, Dict, List, Optional
from datetime import date
from pydantic import BaseModel


class SalesOrderLineCreate(BaseModel):
    lineType: Optional[str] = None
    lineObjectNumber: Optional[str] = None
    description: Optional[str] = None
    unitOfMeasureCode: Optional[str] = None
    quantity: Optional[float] = None
    unitPrice: Optional[float] = None
    discountAmount: Optional[float] = None
    discountPercent: Optional[float] = None
    shipmentDate: Optional[str] = None


class SalesOrderLineUpdate(SalesOrderLineCreate):
    pass


class SalesOrderCreate(BaseModel):
    customerId: Optional[str] = None
    customerNumber: Optional[str] = None
    lines: Optional[List[Dict[str, Any]]] = None
    externalDocumentNumber: Optional[str] = None
    orderDate: Optional[date] = None
    postingDate: Optional[date] = None
    billToCustomerId: Optional[str] = None
    billToCustomerNumber: Optional[str] = None
    shipToName: Optional[str] = None
    shipToContact: Optional[str] = None
    sellToAddressLine1: Optional[str] = None
    sellToAddressLine2: Optional[str] = None
    sellToCity: Optional[str] = None
    sellToCountry: Optional[str] = None
    sellToState: Optional[str] = None
    sellToPostCode: Optional[str] = None
    billToAddressLine1: Optional[str] = None
    billToAddressLine2: Optional[str] = None
    billToCity: Optional[str] = None
    billToCountry: Optional[str] = None
    billToState: Optional[str] = None
    billToPostCode: Optional[str] = None
    shipToAddressLine1: Optional[str] = None
    shipToAddressLine2: Optional[str] = None
    shipToCity: Optional[str] = None
    shipToCountry: Optional[str] = None
    shipToState: Optional[str] = None
    shipToPostCode: Optional[str] = None
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None
    currencyId: Optional[str] = None
    currencyCode: Optional[str] = None
    paymentTermsId: Optional[str] = None
    shipmentMethodId: Optional[str] = None
    salesperson: Optional[str] = None
    partialShipping: Optional[bool] = None
    requestedDeliveryDate: Optional[date] = None
    discountAmount: Optional[float] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None


class SalesOrderUpdate(BaseModel):
    externalDocumentNumber: Optional[str] = None
    orderDate: Optional[date] = None
    postingDate: Optional[date] = None
    customerId: Optional[str] = None
    customerNumber: Optional[str] = None
    billToCustomerId: Optional[str] = None
    billToCustomerNumber: Optional[str] = None
    shipToName: Optional[str] = None
    shipToContact: Optional[str] = None
    sellToAddressLine1: Optional[str] = None
    sellToAddressLine2: Optional[str] = None
    sellToCity: Optional[str] = None
    sellToCountry: Optional[str] = None
    sellToState: Optional[str] = None
    sellToPostCode: Optional[str] = None
    billToAddressLine1: Optional[str] = None
    billToAddressLine2: Optional[str] = None
    billToCity: Optional[str] = None
    billToCountry: Optional[str] = None
    billToState: Optional[str] = None
    billToPostCode: Optional[str] = None
    shipToAddressLine1: Optional[str] = None
    shipToAddressLine2: Optional[str] = None
    shipToCity: Optional[str] = None
    shipToCountry: Optional[str] = None
    shipToState: Optional[str] = None
    shipToPostCode: Optional[str] = None
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None
    currencyId: Optional[str] = None
    currencyCode: Optional[str] = None
    paymentTermsId: Optional[str] = None
    shipmentMethodId: Optional[str] = None
    salesperson: Optional[str] = None
    partialShipping: Optional[bool] = None
    requestedDeliveryDate: Optional[date] = None
    discountAmount: Optional[float] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
