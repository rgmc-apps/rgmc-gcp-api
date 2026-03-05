"""Trade Portal LMSKU Model."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float


class LMSKU(BaseModel):
    brand_id: int = Field(
        default=0,
        sa_column=Column("BrandId", Integer, primary_key=True )
    )
    sku_code: Optional[str] = Field(
        default="",
        sa_column=Column("SkuCode", String)
    )
    barcode: Optional[str] = Field(
        default="",
        sa_column=Column("Barcode", String)
    )
    sku_desc: Optional[str] = Field(
        default="",
        sa_column=Column("SkuDesc", String )
    )
    unit_price: Optional[float] = Field(
        default=0,
        sa_column=Column("UnitPrice", Float , primary_key=True)
    )
    stock_number: Optional[str] = Field(
        default="",
        sa_column=Column("StockNumber", String, primary_key=True)
    )
    color_code: Optional[str] = Field(
        default="",
        sa_column=Column("ColorCode", String, primary_key=True)
    )
    vendor_barcode: str = Field(
        default="",
        sa_column=Column("VendorBarcode", String)
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column("IsActive", Boolean)
    )
    create_by: str = Field(
        default="",
        sa_column=Column("CreateBy", String)
    )
    size_code: str = Field(
        default="",
        sa_column=Column("SizeCode", String, primary_key=True)
    )
    create_date: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("CreateDate", DateTime)
    )
    update_by: str = Field(
        default="",
        sa_column=Column("UpdateBy", String)
    )
    update_date: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column("UpdateDate", DateTime)
    )