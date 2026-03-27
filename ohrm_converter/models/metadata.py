"""Metadata models for root dataset info."""
from pydantic import BaseModel


class Html(BaseModel):
    title: str | None = None
    creator: str | None = None
    description: str | None = None


class HtmlMetadata(BaseModel):
    name: str | None = None
    scheme: str | None = None
    lang: str | None = None
    content: str | None = None
    x_ref: str | None = None
