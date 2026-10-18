import datetime as dt
import os
import uuid
from urllib.parse import parse_qs, urlencode

import dotenv
from flask import (
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.datastructures import ImmutableMultiDict

from ..forms import PewSheetForm
from ..models import Feast, Music, Service
from ..utils import cache_dir, logger
from pydantic import ValidationError

__all__ = [
    "pew_sheet_clear_history_endpoint",
    "pew_sheet_create_view",
    "pew_sheet_default_items_endpoint",
    "pew_sheet_docx_view",
]

dotenv.load_dotenv()
COOKIE_NAME = os.environ.get("COOKIE_NAME", "previousPewSheets")


def pew_sheet_create_view():
    if request.method == "POST" and request.is_json:
        form = None
        try:
            data = dict(request.get_json())
            # Accept slugs for feasts so the client doesn't have to serialise
            # whole feast objects.
            if isinstance(data.get("primary_feast"), str):
                data["primary_feast"] = Feast.get(slug=data["primary_feast"])
            secondary = data.get("secondary_feasts") or []
            data["secondary_feasts"] = [
                Feast.get(slug=s) if isinstance(s, str) else s for s in secondary
            ]
            # Hymns come in as refs (strings) or objects.
            for key in ("introit_hymn", "offertory_hymn", "recessional_hymn"):
                val = data.get(key)
                if isinstance(val, str):
                    data[key] = Music.get_neh_hymn_by_ref(val) if val else None
            # Anthem is a Music or a dict.
            a = data.get("anthem")
            if isinstance(a, dict):
                data["anthem"] = Music(**a)
            service = Service.model_validate(data)
        except ValidationError as exc:
            flash("Sorry, I could not create a service from that data.", "danger")
            for err in exc.errors():
                flash(f"{err['loc']}: {err['msg']}", "danger")
            service = None
    else:
        form = PewSheetForm(request.args)
        if not form.primary_feast.data:
            form.primary_feast.data = Feast.next().slug
        service = None
        if form.validate_on_submit():
            service = Service.from_form(form)

    # Build a flat form so the template still has something to render.
    if form is None:
        form = PewSheetForm()
        if service is not None:
            form.title.data = service.title
            form.date.data = service.date
            form.time.data = service.time
            form.primary_feast.data = service.primary_feast.slug
            form.secondary_feasts.data = [f.slug for f in service.secondary_feasts]
            form.celebrant.data = service.celebrant
            form.preacher.data = service.preacher
            ih = service.introit_hymn
            form.introit_hymn.data = ih.ref if ih else ""
            oh = service.offertory_hymn
            form.offertory_hymn.data = oh.ref if oh else ""
            rh = service.recessional_hymn
            form.recessional_hymn.data = rh.ref if rh else ""
            if service.anthem:
                form.anthem_group.title.data = service.anthem.title
                form.anthem_group.composer.data = service.anthem.composer or ""
                form.anthem_group.lyrics.data = service.anthem.lyrics or ""
                form.anthem_group.translation.data = service.anthem.translation or ""

    stored_history = session.get(COOKIE_NAME, [])
    stored_history = set(stored_history)
    if service is not None and request.method != "POST":
        stored_history.add(urlencode(request.args))
    stored_history = list(stored_history)
    session[COOKIE_NAME] = stored_history

    previous_services = []
    for x in stored_history:
        try:
            args = ImmutableMultiDict(parse_qs(x, keep_blank_values=True))
            previous_service = Service.from_form(PewSheetForm(args))
            previous_services.append((urlencode(args), previous_service))
        except Exception as exc:  # FIXME(BLE001): bad history entries are skipped
            logger.warning(exc)

    previous_services.sort(key=lambda args_service: args_service[1].date)

    return render_template(
        "pewSheet.html", form=form, service=service, previous_services=previous_services
    )


def pew_sheet_clear_history_endpoint():
    session[COOKIE_NAME] = {}
    return make_response("", 204)


def pew_sheet_docx_view():
    if request.method == "POST" and request.is_json:
        try:
            data = dict(request.get_json())
            # Accept slugs for feasts so the client doesn't have to serialise
            # whole feast objects.
            if isinstance(data.get("primary_feast"), str):
                data["primary_feast"] = Feast.get(slug=data["primary_feast"])
            secondary = data.get("secondary_feasts") or []
            data["secondary_feasts"] = [
                Feast.get(slug=s) if isinstance(s, str) else s for s in secondary
            ]
            # Hymns come in as refs (strings) or objects.
            for key in ("introit_hymn", "offertory_hymn", "recessional_hymn"):
                val = data.get(key)
                if isinstance(val, str):
                    data[key] = Music.get_neh_hymn_by_ref(val) if val else None
            # Anthem is a Music or a dict.
            a = data.get("anthem")
            if isinstance(a, dict):
                data["anthem"] = Music(**a)
            service = Service.model_validate(data)
        except ValidationError as exc:
            flash("Sorry, I could not create a service from that data.", "danger")
            for err in exc.errors():
                flash(f"{err['loc']}: {err['msg']}", "danger")
            return redirect(url_for("pew_sheet_create_view"), 400)
    else:
        form = PewSheetForm(request.args)
        if not form.validate_on_submit():
            flash(
                "Sorry, I could not create a service from that information. "
                "Please check the values that you provided.",
                "danger",
            )
            for k, es in form.errors.items():
                for e in es:
                    flash(f"{k}: {e}", "danger")
            return redirect(
                url_for("pew_sheet_create_view") + "?" + urlencode(request.args), 400
            )
        service = Service.from_form(form)

    datestamp = service.date.strftime("%Y-%m-%d")

    filename = f"{datestamp} {service.title}.docx"
    temp_docx = os.path.join(cache_dir, f"pew_sheet_{uuid.uuid4()!s}.docx")
    service.create_docx(temp_docx)
    return send_file(temp_docx, as_attachment=True, download_name=filename)


def pew_sheet_default_items_endpoint():
    if request.method == "POST" and request.is_json:
        data = request.get_json()
    else:
        data = request.args.to_dict()

    primary_slug = data.get("primary_feast")
    if not primary_slug:
        return {"error": "primary_feast is required"}, 400

    primary_feast = Feast.get(slug=primary_slug)
    secondary_slugs = data.get("secondary_feasts") or []
    if isinstance(secondary_slugs, str):
        secondary_slugs = [s for s in secondary_slugs.split(",") if s]
    secondary_feasts = [Feast.get(slug=s) for s in secondary_slugs if s]

    introit_hymn = Music.get_neh_hymn_by_ref(data.get("introit_hymn") or "")
    offertory_hymn = Music.get_neh_hymn_by_ref(data.get("offertory_hymn") or "")
    recessional_hymn = Music.get_neh_hymn_by_ref(data.get("recessional_hymn") or "")

    anthem = None
    ag = data.get("anthem_group") or {}
    if ag.get("title"):
        anthem = Music(
            title=ag.get("title") or "",
            composer=ag.get("composer"),
            lyrics=ag.get("lyrics"),
            category="Anthem",
            ref=None,
            translation=ag.get("translation"),
        )

    service = Service(
        title=data.get("title") or "",
        date=data.get("date") or dt.date.today(),
        time=data.get("time") or dt.time(11, 0),
        celebrant=data.get("celebrant") or "",
        preacher=data.get("preacher") or "",
        primary_feast=primary_feast,
        secondary_feasts=secondary_feasts,
        introit_hymn=introit_hymn,
        offertory_hymn=offertory_hymn,
        recessional_hymn=recessional_hymn,
        anthem=anthem,
    )
    return {"items": [item.model_dump() for item in service.items]}
