import datetime as dt
import re
import typing
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Literal

import jinja2
import yaml
from docx import Document
from docxtpl import DocxTemplate, RichText
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .dateexpr import parse
from .models_base import NotFoundError, get
from .paths import FEASTS_DIR, PEW_SHEET_TEMPLATE
from .utils import NoPandasError, get_neh_df, logger

if typing.TYPE_CHECKING:
    from .forms import PewSheetForm

# Any one year will do for validating a date expression, so pin one to keep
# the verdict from depending on when the feast files happen to be loaded.
VALIDATION_YEAR = 2024


class PypewModel(BaseModel):
    """Base class for the app's models.

    ``extra="forbid"`` rejects unknown fields, so a mistyped key in a feast
    YAML file is reported instead of silently dropped.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _none2datemax(d: dt.date | None) -> dt.date:
    """Put unspecified dates at the end of the list."""
    if d is None:
        return dt.date.max
    return d


class Feast(PypewModel):
    slug: str
    name: str

    # Date expression giving the date of the feast, e.g. "Easter",
    # "8 weeks after Easter" or "25 December". None for feasts that are not
    # tied to a date of their own.
    dateexpr: str | None = None

    introit: str | None = None
    collect: str | None = None
    epistle_ref: str | None = None
    epistle: str | None = None
    gat: str = ""
    gradual: str | None = None
    alleluia: str | None = None
    tract: str | None = None
    gospel_ref: str | None = None
    gospel: str | None = None
    offertory: str | None = None
    communion: str | None = None

    @classmethod
    def from_yaml(cls, slug: str) -> "Feast":
        return _feast_from_yaml(slug)

    @classmethod
    def all(cls) -> list["Feast"]:
        with open(FEASTS_DIR / "_list.txt") as f:
            slugs = [x.strip() for x in f]
            return [cls.from_yaml(slug) for slug in slugs]

    @classmethod
    def upcoming(cls, date: dt.date | None = None) -> list["Feast"]:
        if date is None:
            # FIXME(DTZ011): naive local date is correct here
            date = dt.date.today()

        return sorted(Feast.all(), key=lambda f: _none2datemax(f.get_next_date(date)))

    @classmethod
    def next(cls, date: dt.date | None = None) -> "Feast":
        if date is None:
            # FIXME(DTZ011): naive local date is correct here
            date = dt.date.today()

        return min(Feast.all(), key=lambda f: _none2datemax(f.get_next_date(date)))

    @classmethod
    def get(cls, **kwargs) -> "Feast":
        return get(cls.all(), **kwargs)

    @field_validator("dateexpr")
    @classmethod
    def _valid_dateexpr(cls, v: str | None) -> str | None:
        """Reject an unparseable expression when the feast is loaded.

        Otherwise a typo in a feast file stays hidden until someone opens
        that feast, where the error names no feast at all.
        """
        if v is None:
            return None
        try:
            parse(v, VALIDATION_YEAR)
        except Exception as exc:  # FIXME(BLE001): dateexpr raises several types
            raise ValueError(f"invalid date expression {v!r}: {exc}") from exc
        return v

    def get_date(self, year: int | None = None) -> dt.date | None:
        if self.dateexpr is None:
            return None

        if year is None:
            # FIXME(DTZ005): local wall-clock year, timezone irrelevant
            year = dt.datetime.now().year

        return parse(self.dateexpr, year)

    @property
    def date(self) -> dt.date | None:
        """The date of the feast in the present year."""
        return self.get_date()

    def get_next_date(self, d: dt.date | None = None) -> dt.date | None:
        """Returns the next occurrence of this feast from the specified
        date, which may be in the next calendar year.
        """
        if d is None:
            # FIXME(DTZ011): naive local date is correct here
            d = dt.date.today()

        next_occurrence = self.get_date(year=d.year)
        if next_occurrence is None:
            return None
        if (next_occurrence - d).days < 0:
            next_occurrence = self.get_date(year=d.year + 1)

        return next_occurrence

    @property
    def next_date(self) -> dt.date | None:
        """The next occurrence of the feast, which may be in the next
        calendar year.
        """
        return self.get_next_date()

    def create_docx(self, path) -> None:
        document = Document()
        document.add_heading(self.name, 0)
        document.save(path)


class PewSheetItem(PypewModel, ABC):
    """A block of a pew sheet: a heading, an optional subtitle and some
    paragraphs.

    Subclasses expose ``title``, ``subtitle`` and ``paragraphs``, either as
    fields or as computed properties, so that jinja templates and the
    docx renderer can treat every block the same way.
    """

    @abstractmethod
    def as_richtext(self) -> RichText:
        raise NotImplementedError


class CharacterStyles:
    # FIXME(RUF012): these are lookup tables, not per-instance state
    title = {"font": "Merriweather", "size": 20, "bold": True}
    subtitle = {"font": "Raleway", "size": 18, "italic": True}
    paragraph = {"font": "Cambria", "size": 20}


class Music(PypewModel):
    title: str
    category: Literal["Anthem", "Hymn", "Plainsong"]
    composer: str | None = None
    lyrics: str | None = None
    ref: str | None = None
    translation: str | None = None

    @classmethod
    def neh_hymns(cls) -> list["Music"]:
        try:
            records = get_neh_df().itertuples()
        except NoPandasError as exc:
            logger.warning(exc)
            return []

        def nehref2num(nehref: str) -> tuple[int, str]:
            m = re.match(r"NEH: (\d+)([a-z]?)", nehref)
            assert m is not None
            num, suffix = m.groups()
            return int(num), suffix

        hymns = [
            Music(
                title=record.firstLine,
                category="Hymn",
                composer=None,
                lyrics=None,
                ref=f"NEH: {record.number}",
                # FIXME(E501): long f-string, not splittable by the formatter
                translation=f"Words/translation available at NEH: {record.number}, {record.firstLine}",
            )
            for record in records
        ]
        hymns.sort(key=lambda m: nehref2num(m.ref or ""))
        return hymns

    @classmethod
    def get_neh_hymn_by_ref(cls, ref: str) -> "Music | None":
        try:
            return next(filter(lambda h: h.ref == ref, cls.neh_hymns()))
        except StopIteration:
            return None

    def __str__(self) -> str:
        if self.category == "Hymn":
            return f"{self.ref}, {self.title}"
        if self.composer:
            return f"{self.title} ({self.composer})"
        return self.title

    def as_richtext(self) -> RichText:
        if self.category != "Hymn":
            return RichText(str(self))

        assert self.ref is not None

        rt = RichText()
        rt.add(self.ref + ", ", **CharacterStyles.paragraph)
        rt.add(self.title, **CharacterStyles.paragraph, italic=True)
        return rt


class ServiceItem(PewSheetItem):
    title: str = ""
    paragraphs: list[typing.Any] = Field(default_factory=list)
    subtitle: str | None = None

    def as_richtext(self) -> RichText:

        rt = RichText()
        rt.add(self.title, **CharacterStyles.title)
        if self.subtitle is not None:
            rt.add("\a")
            rt.add(self.subtitle, **CharacterStyles.subtitle)

        for paragraph in self.paragraphs:
            rt.add("\a")
            rt.add(paragraph, **CharacterStyles.paragraph)

        return rt


class CollectItem(PewSheetItem):
    collects: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def title(self) -> str:
        return "Collect" if len(self.collects) == 1 else "Collects"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def subtitle(self) -> str | None:
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def paragraphs(self) -> list[str]:
        return self.collects

    def as_richtext(self) -> RichText:
        rt = RichText()
        rt.add(self.title, **CharacterStyles.title)
        for collect in self.collects:
            if collect.endswith("Amen."):
                rt.add("\a" + collect[:-5], **CharacterStyles.paragraph)
                rt.add(collect[-5:], **CharacterStyles.paragraph, bold=True)
            else:
                rt.add("\a" + collect, **CharacterStyles.paragraph)

        return rt


class MusicItem(PewSheetItem):
    title: str
    music: Music

    @computed_field  # type: ignore[prop-decorator]
    @property
    def subtitle(self) -> str | None:
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def paragraphs(self) -> list[str]:
        return [str(self.music)]

    def as_richtext(self) -> RichText:
        rt = RichText()
        rt.add(self.title, font="Merriweather", size=20, bold=True)
        rt.add("\a")
        rt.add(self.music.as_richtext())
        return rt


class Service(PypewModel):
    # Mandatory fields first, then fields with default values.
    title: str
    date: dt.date
    primary_feast: Feast
    time: dt.time = dt.time(11, 0)
    secondary_feasts: list[Feast] = Field(default_factory=list)
    celebrant: str = ""
    preacher: str = ""
    introit_hymn: Music | None = None
    offertory_hymn: Music | None = None
    recessional_hymn: Music | None = None
    anthem: Music | None = None
    service_type: str = "Sung Mass"

    # One can't call methods in jinja2 templates, so one must provide
    # everything as member properties instead.

    @property
    def collects(self) -> list[str]:
        out = []
        if self.primary_feast.collect:
            out.append(self.primary_feast.collect)
        for sf in self.secondary_feasts:
            if sf.collect:
                out.append(sf.collect)

        # Collects for Advent I and Ash Wednesday are repeated
        # throughout Advent and Lent respectively.
        advent1 = Feast.get(name="Advent I")
        ash_wednesday = Feast.get(name="Ash Wednesday")

        if "Advent" in self.primary_feast.name and self.primary_feast != advent1:
            out.append(advent1.collect)

        if "Lent" in self.primary_feast.name:
            out.append(ash_wednesday.collect)

        return out

    # TODO primary or secondary?
    @property
    def introit_proper(self) -> str | None:
        return self.primary_feast.introit

    @property
    def gat(self) -> str:
        assert self.primary_feast.gat is not None
        return self.primary_feast.gat

    @property
    def gat_propers(self) -> list[str]:
        propers = []
        if "Gradual" in self.primary_feast.gat:
            assert self.primary_feast.gradual is not None
            propers.append(self.primary_feast.gradual)
        if "Alleluia" in self.primary_feast.gat:
            assert self.primary_feast.alleluia is not None
            propers.append(self.primary_feast.alleluia)
        if "Tract" in self.primary_feast.gat:
            assert self.primary_feast.tract is not None
            propers.append(self.primary_feast.tract)
        return propers

    @property
    def offertory_proper(self) -> str | None:
        return self.primary_feast.offertory

    @property
    def communion_proper(self) -> str | None:
        return self.primary_feast.communion

    @property
    def epistle_ref(self) -> str | None:
        return self.primary_feast.epistle_ref

    @property
    def epistle(self) -> str | None:
        return self.primary_feast.epistle

    @property
    def gospel_ref(self) -> str | None:
        return self.primary_feast.gospel_ref

    @property
    def gospel(self) -> str | None:
        return self.primary_feast.gospel

    @property
    def items(self) -> list[PewSheetItem]:
        items: list[PewSheetItem] = []
        if self.introit_hymn:
            items.append(MusicItem(title="Introit Hymn", music=self.introit_hymn))
        items.append(
            ServiceItem(title="Introit Proper", paragraphs=[self.introit_proper])
        )

        collects = CollectItem(collects=self.collects)
        items.append(collects)

        items.append(
            ServiceItem(
                title="Epistle",
                paragraphs=[self.epistle],
                subtitle=self.epistle_ref,
            )
        )
        items.append(ServiceItem(title=self.gat, paragraphs=self.gat_propers))
        items.append(
            ServiceItem(
                title="Gospel", paragraphs=[self.gospel], subtitle=self.gospel_ref
            )
        )

        items.append(
            ServiceItem(title="Offertory Proper", paragraphs=[self.offertory_proper])
        )
        if self.offertory_hymn:
            items.append(MusicItem(title="Offertory Hymn", music=self.offertory_hymn))

        items.append(
            ServiceItem(title="Communion Proper", paragraphs=[self.communion_proper])
        )

        if self.anthem:
            items.append(
                ServiceItem(
                    title="Anthem",
                    paragraphs=[self.anthem.lyrics, self.anthem.translation],
                    subtitle=f"{self.anthem.title}. {self.anthem.composer}",
                )
            )

        if self.recessional_hymn:
            items.append(
                MusicItem(title="Recessional Hymn", music=self.recessional_hymn)
            )

        return items

    @classmethod
    def from_form(cls, form: "PewSheetForm") -> "Service":
        primary_feast = Feast.get(slug=form.primary_feast.data)
        if form.secondary_feasts.data:
            secondary_feasts = [
                Feast.get(slug=slug) for slug in form.secondary_feasts.data if slug
            ]
        else:
            secondary_feasts = []

        ag = form.anthem_group
        # The browser submits every form field, so an anthem group reports
        # data even when the user left it blank; the title is what decides
        # whether there is an anthem at all.
        if ag.title.data:
            anthem = Music(
                title=ag.title.data,
                composer=ag.composer.data,
                lyrics=ag.lyrics.data,
                category="Anthem",
                ref=None,
                translation=ag.translation.data,
            )
        else:
            anthem = None

        return Service(
            title=form.title.data or "",
            date=form.date.data,
            time=form.time.data,
            celebrant=form.celebrant.data or "",
            preacher=form.preacher.data or "",
            primary_feast=primary_feast,
            secondary_feasts=secondary_feasts,
            introit_hymn=Music.get_neh_hymn_by_ref(form.introit_hymn.data),
            offertory_hymn=Music.get_neh_hymn_by_ref(form.offertory_hymn.data),
            recessional_hymn=Music.get_neh_hymn_by_ref(form.recessional_hymn.data),
            anthem=anthem,
        )

    def create_docx(self, path) -> None:
        doc = DocxTemplate(PEW_SHEET_TEMPLATE)
        jinja_env = jinja2.Environment(autoescape=True)
        jinja_env.globals["len"] = len

        # local import to avoid circular import
        from .filters import filters_context

        jinja_env.filters.update(filters_context)
        doc.render({"service": self}, jinja_env)
        doc.save(path)


@lru_cache
def _feast_from_yaml(slug: str) -> Feast:
    path = (FEASTS_DIR / slug).with_suffix(".yaml")
    if not path.is_file():
        raise NotFoundError({"slug": slug})
    with open(path) as f:
        info = yaml.safe_load(f)
        return Feast.model_validate({"slug": slug, **info})
