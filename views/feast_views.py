import datetime
import os
import uuid

import cattrs
from flask import flash, jsonify, make_response, render_template, request, send_file

from filters import english_date
from models import Feast
from models_base import NotFoundError, get
from utils import cache_dir, str2date

__all__ = [
    "feast_date_api",
    "feast_detail_api",
    "feast_detail_view",
    "feast_docx_view",
    "feast_index_api",
    "feast_index_view",
    "feast_upcoming_api",
]


def feast_index_view():
    feasts = Feast.all()
    return render_template("feasts.html", feasts=feasts)


def feast_index_api():
    feasts = Feast.all()
    return jsonify(cattrs.unstructure(feasts))


def feast_upcoming_api():
    """API to get a list of upcoming feasts relative to the specified
    date, with the soonest first.
    """
    s = request.args.get("date")
    if s is not None:
        try:
            date = str2date(s)
        except ValueError:
            return make_response(f"Bad date {s}", 400)
    else:
        date = datetime.date.today()

    sorted_feasts = enumerate(Feast.upcoming(date))
    return jsonify(
        [
            {
                "index": n,
                "slug": f.slug,
                "name": f.name,
                "next": english_date(f.get_next_date(date)),
            }
            for n, f in sorted_feasts
        ]
    )


def feast_date_api(slug):
    try:
        year = request.args.get("year")
        feast = Feast.from_yaml(slug)
        date = feast.get_date(year=year)
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


def feast_detail_api(slug):
    try:
        feasts = Feast.all()
        feast = get(feasts, slug=slug)
    except NotFoundError:
        flash(f"Feast {slug} not found.", "warning")
        return make_response(feast_index_view(), 404)

    return jsonify(cattrs.unstructure(feast))


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
