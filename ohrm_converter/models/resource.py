"""Resource-related models."""
from pydantic import BaseModel


class ArcResource(BaseModel):
    arcid: str
    repid: str | None = None
    arrepref: str | None = None
    arrepreflink: str | None = None
    artitle: str | None = None
    ardescription: str | None = None
    arlanguage: str | None = None
    arstartdate: str | None = None
    arsdatemod: str | None = None
    arstart: str | None = None
    arenddate: str | None = None
    aredatemod: str | None = None
    arend: str | None = None
    arquantityl: float | None = None
    arquantityn: int | None = None
    arquantityt: str | None = None
    arformats: str | None = None
    araccess: str | None = None
    arotherfa: str | None = None
    arref: str | None = None
    arappenddate: str | None = None
    arlastmodd: str | None = None
    arprepared: str | None = None
    arcreator: str | None = None
    arlevel: str | None = None
    arsubtitle: str | None = None
    arprocessing: str | None = None
    arstatus: str | None = None


class DObject(BaseModel):
    doid: str
    dotype: str | None = None
    dotitle: str | None = None
    dodescription: str | None = None
    dostartdate: str | None = None
    dosdatemod: str | None = None
    dostart: str | None = None
    doenddate: str | None = None
    doedatemod: str | None = None
    doend: str | None = None
    doplace: str | None = None
    dophysdesc: str | None = None
    docreator: str | None = None
    docontrol: str | None = None
    arcid: str | None = None
    pubid: str | None = None
    doreference: str | None = None
    dorights: str | None = None
    donotes: str | None = None
    dostatus: str | None = None
    doprepared: str | None = None
    doappenddate: str | None = None
    dolastmodd: str | None = None
    dointerpretation: str | None = None


class DObjectVersion(BaseModel):
    doid: str | None = None
    dovtype: str | None = None
    dovformat: str | None = None
    dovdefault: int | None = None
    dov: str | None = None
    dovattributes: str | None = None
    dovtitle: str | None = None
    dovdescription: str | None = None
    dovstartdate: str | None = None
    dovsdatemod: str | None = None
    dovstart: str | None = None
    dovenddate: str | None = None
    dovedatemod: str | None = None
    dovend: str | None = None
    dovplace: str | None = None
    dovphysdesc: str | None = None
    dovcreator: str | None = None
    dovcontrol: str | None = None
    arcid: str | None = None
    pubid: str | None = None
    dovreference: str | None = None
    dovrights: str | None = None
    dovnotes: str | None = None
    dovstatus: str | None = None
    dovappenddate: str | None = None
    dovlastmodd: str | None = None
    dovimagedisplay: int | None = None
    dovorder: int | None = None
    dovportrait: int | None = None


class PubResource(BaseModel):
    pubid: str
    online: int | None = None
    type: str | None = None
    author: str | None = None
    x_year: str | None = None
    title: str | None = None
    secondaryauthor: str | None = None
    secondarytitle: str | None = None
    placepublished: str | None = None
    publisher: str | None = None
    volume: str | None = None
    numberofvolumes: str | None = None
    number: str | None = None
    pagenos: str | None = None
    edition: str | None = None
    x_date: str | None = None
    typeofwork: str | None = None
    isbn_issn: str | None = None
    source: str | None = None
    abstract: str | None = None
    notes: str | None = None
    classification: str | None = None
    url: str | None = None
    urltype: str | None = None
    urldate: str | None = None
    format: str | None = None
    x_language: str | None = None
    contains: str | None = None
    pubappenddate: str | None = None
    publastmodd: str | None = None
    descriptionofwork: str | None = None
    prepared: str | None = None
    catid: str | None = None
    processing: str | None = None
    status: str | None = None
