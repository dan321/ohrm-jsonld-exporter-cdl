"""Entity-related models."""
from pydantic import BaseModel


class Entity(BaseModel):
    eid: str
    ecountrycode: str | None = None
    eorgcode: str | None = None
    etype: str | None = None
    ename: str | None = None
    esubname: str | None = None
    elegalno: str | None = None
    estartdate: str | None = None
    esdatemod: str | None = None
    estart: str | None = None
    eenddate: str | None = None
    eedatemod: str | None = None
    eend: str | None = None
    edatequal: str | None = None
    ebthplace: str | None = None
    ebthstate: str | None = None
    ebthcountry: str | None = None
    edthplace: str | None = None
    edthstate: str | None = None
    edthcountry: str | None = None
    elocation: str | None = None
    elegalstatus: str | None = None
    enationality: str | None = None
    efunction: str | None = None
    esumnote: str | None = None
    efullnote: str | None = None
    egender: str | None = None
    ereference: str | None = None
    enote: str | None = None
    eappenddate: str | None = None
    eprepared: str | None = None
    elastmodd: str | None = None
    elogo: str | None = None
    eurl: str | None = None
    earchives: int | None = None
    epub: int | None = None
    eonline: int | None = None
    egallery: int | None = None
    eowner: str | None = None
    erating: float | None = None
    estatus: str | None = None
    x_efunction: str | None = None


class EntityEvent(BaseModel):
    eid: str | None = None
    eedescription: str | None = None
    eelocation: str | None = None
    eegis: str | None = None
    eestartdate: str | None = None
    eesdatemod: str | None = None
    eestart: str | None = None
    eeenddate: str | None = None
    eeedatemod: str | None = None
    eeend: str | None = None
    eedatequal: str | None = None
    eenote: str | None = None
    eerating: float | None = None
    eeappenddate: str | None = None
    eelastmodd: str | None = None
    eeprepared: str | None = None
    eetype: str | None = None
    otdid: str | None = None


class EntityName(BaseModel):
    eid: str | None = None
    enalternate: str | None = None
    enalternatetype: str | None = None
    enstartdate: str | None = None
    ensdatemod: str | None = None
    enstart: str | None = None
    enenddate: str | None = None
    enedatemod: str | None = None
    enend: str | None = None
    endatequal: str | None = None
    enplace: str | None = None
    ennote: str | None = None
