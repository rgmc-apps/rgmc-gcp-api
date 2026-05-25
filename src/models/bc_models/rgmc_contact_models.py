"""RGMC custom API — Contact Pydantic models (Pag50203)."""
from typing import Optional
from pydantic import BaseModel


class RgmcContactCreate(BaseModel):
    number: Optional[str] = None
    name: Optional[str] = None
    firstName: Optional[str] = None
    middleName: Optional[str] = None
    lastName: Optional[str] = None
    searchName: Optional[str] = None
    type: Optional[str] = None
    companyNo: Optional[str] = None
    jobTitle: Optional[str] = None
    address: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postCode: Optional[str] = None
    countryRegionCode: Optional[str] = None
    phoneNo: Optional[str] = None
    mobilePhoneNo: Optional[str] = None
    email: Optional[str] = None
    salespersonCode: Optional[str] = None


class RgmcContactUpdate(RgmcContactCreate):
    pass
