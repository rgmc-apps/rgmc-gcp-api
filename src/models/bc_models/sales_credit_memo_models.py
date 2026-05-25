"""Business Central Sales Credit Memo Pydantic models."""
from typing import Optional
from datetime import date
from pydantic import BaseModel


class SalesCreditMemoCreate(BaseModel):
    externalDocumentNumber: Optional[str] = None
    creditMemoDate: Optional[date] = None
    postingDate: Optional[date] = None
    dueDate: Optional[date] = None
    customerId: Optional[str] = None
    customerNumber: Optional[str] = None
    billToCustomerId: Optional[str] = None
    billToCustomerNumber: Optional[str] = None
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
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None
    currencyId: Optional[str] = None
    currencyCode: Optional[str] = None
    paymentTermsId: Optional[str] = None
    shipmentMethodId: Optional[str] = None
    salesperson: Optional[str] = None
    discountAmount: Optional[float] = None
    discountAppliedBeforeTax: Optional[bool] = None
    invoiceId: Optional[str] = None
    invoiceNumber: Optional[str] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
    customerReturnReasonId: Optional[str] = None


class SalesCreditMemoUpdate(BaseModel):
    externalDocumentNumber: Optional[str] = None
    creditMemoDate: Optional[date] = None
    postingDate: Optional[date] = None
    dueDate: Optional[date] = None
    customerId: Optional[str] = None
    customerNumber: Optional[str] = None
    billToCustomerId: Optional[str] = None
    billToCustomerNumber: Optional[str] = None
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
    shortcutDimension1Code: Optional[str] = None
    shortcutDimension2Code: Optional[str] = None
    currencyId: Optional[str] = None
    currencyCode: Optional[str] = None
    paymentTermsId: Optional[str] = None
    shipmentMethodId: Optional[str] = None
    salesperson: Optional[str] = None
    discountAmount: Optional[float] = None
    discountAppliedBeforeTax: Optional[bool] = None
    invoiceId: Optional[str] = None
    invoiceNumber: Optional[str] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
    customerReturnReasonId: Optional[str] = None
