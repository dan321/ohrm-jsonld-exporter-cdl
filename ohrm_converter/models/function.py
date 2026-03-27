"""Function model."""
from pydantic import BaseModel


class Function(BaseModel):
    fid: str
    fname: str | None = None
    ffield: str | None = None
    fdescription: str | None = None
    freference: str | None = None
    fstartdate: str | None = None
    fsdatemod: str | None = None
    fstart: str | None = None
    fenddate: str | None = None
    fedatemod: str | None = None
    fend: str | None = None
    fdatequal: str | None = None
    fapplies: str | None = None
    fappenddate: str | None = None
    flastmodd: str | None = None
    fnote: str | None = None
    fparent: str | None = None
