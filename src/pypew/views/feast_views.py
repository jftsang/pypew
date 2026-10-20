import datetime as dt
import json
import os
import uuid
from typing import Any

from flask import (
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_pydantic import validate
from pydantic import BaseModel, ValidationError, field_validator

from ..dateexpr import EXAMPLES
from ..filters import english_date
from ..forms import FeastForm
from ..models import Feast
from ..models_base import NotFoundError, get
from ..paths import FEASTS_DIR
from ..utils import cache_dir

__all__ = [
    "feast_create_api",
    "feast_create_view",
    "feast_date_api",
    "feast_detail_api",
    "feast_detail_view",
    "feast_docx_view",
    "feast_edit_view",
    "feast_index_api",
    "feast_index_view",
    "feast_order_api",
    "feast_order_view",
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


class FeastOrderBody(BaseModel):
    slugs: list[str]


def _feast_exists(slug: str) -> bool:
    return (FEASTS_DIR / f"{slug}.yaml").is_file()


def _order_error(slugs: Any) -> str | None:
    if not isinstance(slugs, list) or not slugs:
        return "The order must be a list of feast slugs."
    if not all(isinstance(slug, str) for slug in slugs):
        return "The order must be a list of feast slugs."
    current = Feast.slugs()
    if len(slugs) != len(current) or set(slugs) != set(current):
        return "The order must contain every feast exactly once."
    return None


def _add_form_errors(form: FeastForm, exc: ValidationError) -> None:
    for error in exc.errors():
        if not error["loc"]:
            continue
        field = getattr(form, str(error["loc"][0]), None)
        if field is not None and hasattr(field, "errors"):
            field.errors.append(error["msg"])


def _invalid_body(errors: list) -> Any:
    return make_response(jsonify({"validation_error": {"body_params": errors}}), 400)


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


def feast_edit_view(slug):
    try:
        feast = get(Feast.all(), slug=slug)
    except NotFoundError:
        flash(f"Feast {slug} not found.", "warning")
        return make_response(feast_index_view(), 404)

    form = FeastForm(request.form, obj=feast)
    if request.method == "POST" and form.validate_on_submit():
        try:
            updated = Feast.from_form(form, slug=slug)
        except ValidationError as exc:
            _add_form_errors(form, exc)
        else:
            updated.save_yaml()
            flash(f"{updated.name} saved.", "success")
            return redirect(url_for("feast_detail_view", slug=slug))

    return render_template("feastForm.html", form=form, feast=feast, examples=EXAMPLES)


def feast_create_view():
    form = FeastForm(request.form)
    if request.method == "POST" and form.validate_on_submit():
        try:
            feast = Feast.from_form(form)
        except ValidationError as exc:
            _add_form_errors(form, exc)
        else:
            if _feast_exists(feast.slug) or feast.slug in Feast.slugs():
                form.slug.errors.append(
                    f"A feast with the slug {feast.slug!r} already exists."
                )
            else:
                feast.save_yaml()
                Feast.save_order(Feast.slugs() + [feast.slug])
                flash(f"{feast.name} created.", "success")
                return redirect(url_for("feast_detail_view", slug=feast.slug))

    return render_template("feastForm.html", form=form, feast=None, examples=EXAMPLES)


def feast_order_view():
    if request.method == "POST":
        try:
            slugs = json.loads(request.form.get("order") or "")
        except ValueError:
            slugs = None
        error = _order_error(slugs)
        if error is None:
            Feast.save_order(slugs)
            flash("Feast order saved.", "success")
            return redirect(url_for("feast_index_view"))
        flash(error, "danger")

    return render_template("feastsOrder.html", feasts=Feast.all())


@validate()
def feast_detail_api(slug):
    if request.method == "PUT":
        if not _feast_exists(slug):
            return make_response(f"Feast {slug} not found", 404)

        body = request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            return _invalid_body(
                [
                    {
                        "loc": ["body"],
                        "msg": "Input should be a valid dictionary.",
                        "type": "model_attributes_type",
                    }
                ]
            )
        if body.get("slug") is not None and body["slug"] != slug:
            return _invalid_body(
                [
                    {
                        "loc": ["slug"],
                        "msg": f"slug must match the path ({slug!r})",
                        "type": "value_error",
                    }
                ]
            )

        try:
            feast = Feast.model_validate({**body, "slug": slug})
        except ValidationError as exc:
            return _invalid_body(exc.errors(include_context=False, include_url=False))
        feast.save_yaml()
        return feast

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


@validate(body=Feast)
def feast_create_api():
    feast = request.body_params
    if _feast_exists(feast.slug) or feast.slug in Feast.slugs():
        return make_response(f"Feast {feast.slug} already exists", 400)
    feast.save_yaml()
    Feast.save_order(Feast.slugs() + [feast.slug])
    return feast, 201


@validate(body=FeastOrderBody)
def feast_order_api():
    slugs = request.body_params.slugs
    error = _order_error(slugs)
    if error is not None:
        return make_response(error, 400)
    Feast.save_order(slugs)
    return jsonify({"slugs": slugs})
