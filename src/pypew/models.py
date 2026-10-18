import datetime as dt
import re
import typing
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Annotated, Literal

import jinja2
import yaml
from docx import Document
from docxtpl import DocxTemplate, RichText
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

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

    ``type`` names the concrete kind of item, both to tell the kinds apart
    in the user interface and to pick the right class when a serialised
    service is read back in.
    """

    type: str

    @abstractmethod
    def as_richtext(self) -> RichText:
        raise NotImplementedError


def _text_richtext(
    title: str, subtitle: str | None, paragraphs: typing.Iterable[typing.Any]
) -> RichText:
    """Render a heading, an optional subtitle and some paragraphs.

    This is how nearly every item is set, so they all share it; only items
    that style their text differently -- hymns, whose title is italicised
    -- render themselves.
    """
    rt = RichText()
    rt.add(title, **CharacterStyles.title)
    if subtitle is not None:
        rt.add("\a")
        rt.add(subtitle, **CharacterStyles.subtitle)

    for paragraph in paragraphs:
        rt.add("\a")
        rt.add(paragraph, **CharacterStyles.paragraph)

    return rt


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
    """An item that doesn't fit any of the more specific categories."""

    type: Literal["misc"] = "misc"
    title: str = ""
    paragraphs: list[typing.Any] = Field(default_factory=list)
    subtitle: str | None = None

    def as_richtext(self) -> RichText:
        return _text_richtext(self.title, self.subtitle, self.paragraphs)


class CollectItem(PewSheetItem):
    type: Literal["collect"] = "collect"
    collects: list[str] = Field(default_factory=list)

    @property
    def title(self) -> str:
        return "Collect" if len(self.collects) == 1 else "Collects"

    @property
    def subtitle(self) -> str | None:
        return None

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


class ProperItem(PewSheetItem):
    """One of the sung or said texts of the proper of the day."""

    type: Literal["proper"] = "proper"
    proper_type: str
    title: str = ""
    paragraphs: list[typing.Any] = Field(default_factory=list)
    subtitle: str | None = None

    def as_richtext(self) -> RichText:
        return _text_richtext(self.title, self.subtitle, self.paragraphs)


class ReadingItem(PewSheetItem):
    """A reading of the scriptures: Old Testament, Epistle or Gospel."""

    type: Literal["reading"] = "reading"
    reading_type: str
    title: str = ""
    paragraphs: list[typing.Any] = Field(default_factory=list)
    subtitle: str | None = None

    def as_richtext(self) -> RichText:
        return _text_richtext(self.title, self.subtitle, self.paragraphs)


class MusicItem(PewSheetItem, ABC):
    """An item of music sung during the service."""

    title: str

    @property
    def subtitle(self) -> str | None:
        return None

    @property
    def paragraphs(self) -> list[str]:
        raise NotImplementedError


class HymnItem(MusicItem):
    type: Literal["hymn"] = "hymn"
    music: Music

    @property
    def paragraphs(self) -> list[str]:
        return [str(self.music)]

    def as_richtext(self) -> RichText:
        rt = RichText()
        rt.add(self.title, font="Merriweather", size=20, bold=True)
        rt.add("\a")
        rt.add(self.music.as_richtext())
        return rt


class AnthemItem(MusicItem):
    """An anthem, as opposed to a hymn: named and attributed to a composer
    rather than picked out of a hymnal.

    ``title`` names the place the anthem occupies in the service, and
    ``name`` is the anthem itself.
    """

    type: Literal["anthem"] = "anthem"
    name: str | None = None
    composer: str | None = None
    lyrics: str | None = None
    translation: str | None = None

    @property
    def paragraphs(self) -> list[str]:
        return [p for p in (self.lyrics, self.translation) if p]

    @property
    def subtitle(self) -> str | None:
        parts = [p for p in (self.name, self.composer) if p]
        return ". ".join(parts) or None

    def as_richtext(self) -> RichText:
        return _text_richtext(self.title, self.subtitle, self.paragraphs)


PewSheetItemUnion = Annotated[
    ServiceItem | CollectItem | ProperItem | ReadingItem | HymnItem | AnthemItem,
    Field(discriminator="type"),
]


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
    items: list[PewSheetItemUnion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _default_items(self) -> "Service":
        """Fall back on the traditional order of service.

        A service that doesn't say what its items are gets the ones implied
        by its feast and its musical choices, so that the traditional form
        and an explicit item list produce the same sheet.
        """
        if not self.items:
            self.items = self.default_items()
        return self

    # One can't call methods in jinja2 templates, so one must provide
    # everything as member properties instead. These read back out of
    # ``items``, so they describe whatever the service actually contains
    # rather than what its feast happens to say.

    def _proper(self, proper_type: str) -> ProperItem | None:
        for item in self.items:
            if isinstance(item, ProperItem) and item.proper_type == proper_type:
                return item
        return None

    def _reading(self, reading_type: str) -> ReadingItem | None:
        for item in self.items:
            if isinstance(item, ReadingItem) and item.reading_type == reading_type:
                return item
        return None

    @property
    def _collect_item(self) -> CollectItem | None:
        for item in self.items:
            if isinstance(item, CollectItem):
                return item
        return None

    @staticmethod
    def _first(item: PewSheetItem | None) -> typing.Any:
        """The one paragraph of a single-paragraph item, if it has one."""
        if item is None or not item.paragraphs:
            return None
        return item.paragraphs[0]

    @property
    def collects(self) -> list[str]:
        item = self._collect_item
        return list(item.collects) if item else []

    # TODO primary or secondary?
    @property
    def introit_proper(self) -> str | None:
        return self._first(self._proper("introit"))

    @property
    def gat(self) -> str:
        item = self._proper("gat")
        return item.title if item else ""

    @property
    def gat_propers(self) -> list[str]:
        item = self._proper("gat")
        return list(item.paragraphs) if item else []

    @property
    def offertory_proper(self) -> str | None:
        return self._first(self._proper("offertory"))

    @property
    def communion_proper(self) -> str | None:
        return self._first(self._proper("communion"))

    @property
    def epistle_ref(self) -> str | None:
        item = self._reading("epistle")
        return item.subtitle if item else None

    @property
    def epistle(self) -> str | None:
        return self._first(self._reading("epistle"))

    @property
    def gospel_ref(self) -> str | None:
        item = self._reading("gospel")
        return item.subtitle if item else None

    @property
    def gospel(self) -> str | None:
        return self._first(self._reading("gospel"))

    def _feast_collects(self) -> list[str]:
        """The collects the traditional order of service would use.

        This reads the feasts directly rather than going through
        ``collects``, which in turn reads the items this builds.
        """
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

    def _feast_gat_propers(self) -> list[str]:
        """The gradual/alleluia/tract texts the feast calls for."""
        propers = []
        gat = self.primary_feast.gat
        if "Gradual" in gat:
            assert self.primary_feast.gradual is not None
            propers.append(self.primary_feast.gradual)
        if "Alleluia" in gat:
            assert self.primary_feast.alleluia is not None
            propers.append(self.primary_feast.alleluia)
        if "Tract" in gat:
            assert self.primary_feast.tract is not None
            propers.append(self.primary_feast.tract)
        return propers

    def default_items(self) -> list[PewSheetItemUnion]:
        """The items of the traditional order of service.

        This is what a service gets when it is built from the feast and the
        handful of musical choices, rather than from an explicit list of
        items.
        """
        f = self.primary_feast
        items: list[PewSheetItemUnion] = []
        if self.introit_hymn:
            items.append(HymnItem(title="Introit Hymn", music=self.introit_hymn))
        items.append(
            ProperItem(
                proper_type="introit",
                title="Introit Proper",
                paragraphs=[f.introit],
            )
        )

        items.append(CollectItem(collects=self._feast_collects()))

        items.append(
            ReadingItem(
                reading_type="epistle",
                title="Epistle",
                paragraphs=[f.epistle],
                subtitle=f.epistle_ref,
            )
        )
        assert f.gat is not None
        items.append(
            ProperItem(
                proper_type="gat",
                title=f.gat,
                paragraphs=self._feast_gat_propers(),
            )
        )
        items.append(
            ReadingItem(
                reading_type="gospel",
                title="Gospel",
                paragraphs=[f.gospel],
                subtitle=f.gospel_ref,
            )
        )

        items.append(
            ProperItem(
                proper_type="offertory",
                title="Offertory Proper",
                paragraphs=[f.offertory],
            )
        )
        if self.offertory_hymn:
            items.append(HymnItem(title="Offertory Hymn", music=self.offertory_hymn))

        items.append(
            ProperItem(
                proper_type="communion",
                title="Communion Proper",
                paragraphs=[f.communion],
            )
        )

        if self.anthem:
            items.append(
                AnthemItem(
                    title="Anthem",
                    name=self.anthem.title,
                    composer=self.anthem.composer,
                    lyrics=self.anthem.lyrics,
                    translation=self.anthem.translation,
                )
            )

        if self.recessional_hymn:
            items.append(
                HymnItem(title="Recessional Hymn", music=self.recessional_hymn)
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
