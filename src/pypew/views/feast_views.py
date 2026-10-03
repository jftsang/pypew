import datetime as dt
import os
import uuid
from typing import Any

from flask import flash, jsonify, make_response, render_template, request, send_file
from flask_pydantic import validate
from pydantic import BaseModel, field_validator

from ..filters import english_date
from ..models import Feast
from ..models_base import NotFoundError, get
from ..utils import cache_dir

__all__ = [
    "feast_date_api",
    "feast_detail_api",
    "feast_detail_view",
    "feast_docx_view",
    "feast_index_api",
    "feast_index_view",
    "feast_upcoming_api",
]


class QueryParams(BaseModel):
    """Base for the API's query-parameter models.

    Unknown parameters are ignored, and a blank parameter means "not given"
    rather than being a validation error.
    """

    @field_validator("*", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any:
        return None if value == "" else value


class FeastUpcomingQuery(QueryParams):
    date: dt.date | None = None


class FeastDateQuery(QueryParams):
    year: int | None = None


class FeastUpcomingItem(BaseModel):
    index: int
    slug: str
    name: str
    next: str


def feast_index_view():
    feasts = Feast.all()
    return render_template("feasts.html", feasts=feasts)


@validate(response_many=True)
def feast_index_api():
    return Feast.all()


@validate(query=FeastUpcomingQuery, response_many=True)
def feast_upcoming_api():
    """API to get a list of upcoming feasts relative to the specified
    date, with the soonest first.
    """
    date = request.query_params.date or dt.date.today()

    return [
        FeastUpcomingItem(
            index=n,
            slug=f.slug,
            name=f.name,
            next=english_date(f.get_next_date(date)),
        )
        for n, f in enumerate(Feast.upcoming(date))
    ]


@validate(query=FeastDateQuery)
def feast_date_api(slug):
    try:
        feast = Feast.from_yaml(slug)
        date = feast.get_date(year=request.query_params.year)
        return jsonify(date.isoformat() if date else None)
    except NotFoundError:
        return make_response(f"Feast {slug} not found", 404)


def feast_detail_view(slug):
    try:
        feasts = Feast.all()
        feast = get(feasts, slug=slug)
    except NotFoundError:
        flash(f"Feast {slug} not found.", "warning")
        return make_response(feast_index_view(), 404)

    return render_template("feastDetails.html", feast=feast, feasts=feasts)


@validate()
def feast_detail_api(slug):
    try:
        feast = get(Feast.all(), slug=slug)
    except NotFoundError:
        flash(f"Feast {slug} not found.", "warning")
        return make_response(feast_index_view(), 404)

    return feast


def feast_docx_view(slug):
    try:
        feast = Feast.get(slug=slug)
    except NotFoundError:
        flash(f"Feast {slug} not found.", "warning")
        return make_response(feast_index_view(), 404)

    filename = f"{feast.name}.docx"
    temp_docx = os.path.join(cache_dir, f"feast_{uuid.uuid4()!s}.docx")
    feast.create_docx(path=temp_docx)
    return send_file(temp_docx, as_attachment=True, download_name=filename)
