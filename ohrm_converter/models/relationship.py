"""Relationship models."""
from pydantic import BaseModel


class EARRship(BaseModel):
    arcid: str | None = None
    eid: str | None = None
    relationship: str | None = None
    description: str | None = None
    rating: float | None = None
    earstartdate: str | None = None
    earsdatemod: str | None = None
    earstart: str | None = None
    earenddate: str | None = None
    earedatemod: str | None = None
    earend: str | None = None
    earplace: str | None = None
    earcitation: str | None = None
    earprepared: str | None = None
    earappenddate: str | None = None
    earlastmodd: str | None = None
    earereference: int | None = None


class EDORship(BaseModel):
    doid: str | None = None
    eid: str | None = None
    relationship: str | None = None
    description: str | None = None
    rating: float | None = None
    edostartdate: str | None = None
    edosdatemod: str | None = None
    edostart: str | None = None
    edoenddate: str | None = None
    edoedatemod: str | None = None
    edoend: str | None = None
    edoplace: str | None = None
    edocitation: str | None = None
    edoprepared: str | None = None
    edoappenddate: str | None = None
    edolastmodd: str | None = None
    edoereference: int | None = None
    edogallery: int | None = None


class EFRship(BaseModel):
    eid: str | None = None
    fid: str | None = None
    description: str | None = None
    rating: int | None = None
    efstartdate: str | None = None
    efsdatemod: str | None = None
    efstart: str | None = None
    efenddate: str | None = None
    efedatemod: str | None = None
    efend: str | None = None
    efplace: str | None = None
    efplacestate: str | None = None
    efplacecountry: str | None = None
    efcitation: str | None = None
    efprepared: str | None = None
    efnote: str | None = None
    efappenddate: str | None = None
    eflastmodd: str | None = None
    ordering: int | None = None


class RelatedEntity(BaseModel):
    eid: str | None = None
    reid: str | None = None
    rerelationship: str | None = None
    redescription: str | None = None
    restartdate: str | None = None
    resdatemod: str | None = None
    restart: str | None = None
    reenddate: str | None = None
    reedatemod: str | None = None
    reend: str | None = None
    redatequal: str | None = None
    renote: str | None = None
    rerating: float | None = None
    reappenddate: str | None = None
    relastmodd: str | None = None
    reprepared: str | None = None
    reorder: int | None = None


class RelatedResource(BaseModel):
    rrno: int
    rtype: str | None = None
    rid: str | None = None
    rrid: str | None = None
    rrdescription: str | None = None
    rrstartdate: str | None = None
    rrsdatemod: str | None = None
    rrstart: str | None = None
    rrenddate: str | None = None
    rredatemod: str | None = None
    rrend: str | None = None
    rrdatequal: str | None = None
    rrnote: str | None = None
    rrrating: float | None = None
    rrappenddate: str | None = None
    rrlastmodd: str | None = None
