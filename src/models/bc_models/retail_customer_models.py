"""RGMC custom API — Retail Customer Pydantic models (Pag50200)."""
from typing import Optional
from pydantic import BaseModel


class RetailCustomerCreate(BaseModel):
    number: Optional[str] = None
    name: Optional[str] = None
    name2: Optional[str] = None
    contact: Optional[str] = None
    phoneNo: Optional[str] = None
    mobilePhoneNo: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postCode: Optional[str] = None
    countryRegionCode: Optional[str] = None
    currencyCode: Optional[str] = None
    creditLimitLcy: Optional[float] = None
    paymentTermsCode: Optional[str] = None
    paymentMethodCode: Optional[str] = None
    vatRegistrationNo: Optional[str] = None
    customerPostingGroup: Optional[str] = None
    genBusPostingGroup: Optional[str] = None
    salespersonCode: Optional[str] = None
    blocked: Optional[str] = None


class RetailCustomerUpdate(RetailCustomerCreate):
    pass
