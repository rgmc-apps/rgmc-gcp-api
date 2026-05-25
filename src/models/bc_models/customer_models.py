"""Business Central Customer Pydantic models."""
from typing import Optional
from pydantic import BaseModel


class CustomerCreate(BaseModel):
    number: Optional[str] = None
    displayName: Optional[str] = None
    type: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    salespersonCode: Optional[str] = None
    creditLimit: Optional[float] = None
    taxLiable: Optional[bool] = None
    taxAreaId: Optional[str] = None
    taxRegistrationNumber: Optional[str] = None
    currencyId: Optional[str] = None
    currencyCode: Optional[str] = None
    paymentTermsId: Optional[str] = None
    shipmentMethodId: Optional[str] = None
    paymentMethodId: Optional[str] = None
    blocked: Optional[str] = None


class CustomerUpdate(BaseModel):
    number: Optional[str] = None
    displayName: Optional[str] = None
    type: Optional[str] = None
    addressLine1: Optional[str] = None
    addressLine2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    salespersonCode: Optional[str] = None
    creditLimit: Optional[float] = None
    taxLiable: Optional[bool] = None
    taxAreaId: Optional[str] = None
    taxRegistrationNumber: Optional[str] = None
    currencyId: Optional[str] = None
    currencyCode: Optional[str] = None
    paymentTermsId: Optional[str] = None
    shipmentMethodId: Optional[str] = None
    paymentMethodId: Optional[str] = None
    blocked: Optional[str] = None
