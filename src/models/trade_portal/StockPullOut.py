"""Trade Portal StockPullOut Model."""

from pydantic import BaseModel, Field
from datetime import datetime, date

class StockPullOut(BaseModel):
    stockpulloutid: int = -1
    pulloutdate: date = Field(default_factory=date.today)
    pullouttype: str = ""
    pulloutnumber: str = ""
    customerid: int = -1
    sourcerefnumber: str = ""
    sourcebrandid: int = -1
    sourcestoreid: int = -1
    sourcesiteid: int = -1
    destnbrandid: int = -1
    destnstoreid: int = -1
    destnsiteid: int = -1
    filepath: str = ""
    downloadby: str = ""
    downloaddate: datetime = Field(default_factory=datetime.now)
    createby: str = ""
    createdate: datetime = Field(default_factory=datetime.now)
    updateby: str = ""
    updatedate: datetime = Field(default_factory=datetime.now)