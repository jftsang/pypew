# Plan: Refactoring Service to use polymorphic service items (backend focus)

## Background

The user wants to genericise the structure of a Service: instead of flat fields, a
Service should consist of a list of "service items". PewSheetItem remains the abstract
base. ServiceItem is the concrete implementation for miscellaneous items. Other item
types (propers, collects, readings - OT/Epistle/Gospel, music with hymn/anthem as
subclasses) need to be modelled with proper polymorphism for
serialization/deserialization. Current structure should remain as the default.

## Goals (backend-focused now)

- Refactor models to support polymorphic service items with Pydantic v2 discriminated
  unions
- Keep all existing `@property` methods on Service working so call sites don't change
  yet
- Maintain current structure as the default when constructing from existing forms/data
- Ensure serialization/deserialization supports polymorphism

## Plan details

### 1. Redesign service item hierarchy

Keep `PewSheetItem` (ABC) as abstract base. It currently has `as_richtext()` abstract.
Add `type`/discriminator fields for polymorphism. With Pydantic v2, use
`discriminator='type'` on unions.

Define new/updated item classes:

- `ServiceItem` (misc) - as is, with `title`, `subtitle`, `paragraphs`
- `CollectItem` - holds collects (may become list of collect strings). Current form is
  fine.
- `ProperItem` or specific proper items? The user says "propers" - could be generic
  `ProperItem(title, paragraphs, subtitle)`. Or separate classes. But easier to have a
  general `ProperItem` that covers Introit Proper, Offertory Proper, Communion Proper,
  GAT sections etc. Or be explicit.
- `ReadingItem` - for OT reading, Epistle, Gospel. Has `title` (e.g. "Epistle","Gospel",
  "Old Testament"), `reference` (or `subtitle`), `text` (paragraphs). Current readings
  in codebase have ref + text.
- `MusicItem` - maybe keep as wrapper around music? Or make Music abstract with
  subclasses. User says "music itself is an abstract class of 'hymn' or 'anthem'". Also
  in current codebase, `Music` is a model with `category`. Could convert to
  discriminated union.
    - Music base (abstract), then `Hymn(music details)`, `Anthem(music details)` as
      subclasses. Then MusicItem could reference them.

But this is a significant redesign. Need to be compatible with existing data.

Also need to handle the fact that in current model, anthem is stored as Music with
category='Anthem', hymns come from NEH lookup.

### 2. Pydantic v2 polymorphism

Use `typing.Annotated` + `Discriminator` or just define union with `discriminator`. Also
need to ensure models serialize with discriminators. For example:

```python
from typing import Literal, Annotated, Union
from pydantic import Field, Discriminator


class BaseItem(PewSheetItem):
    item_type: Literal["misc"] = "misc"


# etc., then union: Item = Annotated[Union[ServiceItem, CollectItem, ...], Field(discriminator='item_type')]
```

### 3. Service model changes

Current Service has flat fields and builds items via `items()` property. The user says
"focus on changing how the Service model is structured on the backend. You can keep the
`@property` methods, so that call sites don't need to be updated; all that will change
for now is that the implementation of these getter methods."

So perhaps add `items` as a stored field (list of polymorphic items) with a default
factory that builds the "default/current structure". Or compute from stored items. Also
keep other properties (collects, introit_proper etc.) for backward compatibility - they
might still be useful. The instruction says keep existing property methods working.

So we need to design: does Service store items explicitly? The new structure is "service
will consist of a list of 'service items'". So items should be a field. And the default
construction should produce the current traditional structure.

So modify Service to have something like:

```python
items: list[ServiceItemUnion] = Field(
    default_factory=lambda: _default_items_from_traditional(...)
)  # but need context
# or compute in model_validator? Or have a way to build defaults
```

But building defaults depends on all the flat fields. Alternatively, keep flat fields
for now as optional with defaults, and compute items from them by default. That
preserves backward compatibility.

Also need to handle deserialization - if someone passes items directly, use them; if
not, build from flat structure. Can use `model_validator(mode='before')` or
`model_validator(mode='after')` depending on approach.

Alternatively, restructure so that items is the canonical source. And provide helper to
construct from traditional form data.

Also need to import discriminated unions properly in v2.

### 4. Rendering compatibility

HTML template iterates over `service.items` and accesses `item.title`, `item.subtitle`,
`item.paragraphs`. This works if each item exposes these as properties (some already do
via computed_fields). Docx uses `as_richtext` filter - all subclasses implement it. So
interface is compatible.

### 5. Testing

All existing tests still need to pass? Let us look at tests - they construct Service
with flat fields, access properties like `service.collects`, `service.items`. So keeping
properties working is key.

### 6. Next steps (after backend refactor as requested)

The user also mentioned frontend form changes, JSON submission etc., but said "focus on
changing how the Service model is structured on the backend" for now. So this plan is
scoped to backend model changes.

### Additional details on item classes

- `ProperItem(type, title, paragraphs, subtitle=None)` - for proper texts like Introit
  Proper, Gradual etc. Could use `type` discriminator or just have generic with title.
- `ReadingItem(type, title, reference/subtitle, text/paragraphs)` - for OT, Epistle,
  Gospel.
- `CollectItem` - keep as is but ensure it's polymorphic.
- `MusicItem` base and subclasses - or split into `HymnItem` and `AnthemItem`. Also need
  to handle the existing `Music` model. Maybe create
  `HymnItem(ref/title/category='Hymn', ...)` and
  `AnthemItem(title, composer, lyrics, translation, category='Anthem')`.

Also need to update the union type and discriminator field names consistently. Use`type`
or `kind` as discriminator.

### Implementation approach

1. First, extend the item hierarchy in models.py with new classes and discriminated
   union
2. Modify Service to store `items` as a field with proper validation
3. Keep all existing flat fields and properties for backward compatibility
4. Provide a way to construct the default items list from traditional Service data
5. Test existing tests still pass

Also consider that when serializing, the discriminator will be included - this is fine
for JSON API responses.

## Questions for user

1. Preferred discriminator field name (`type`, `kind`, `item_type`)?
2. Should we make separate classes for each proper type or use a generic ProperItem with
   a `proper_type` field?
3. For readings, should we have OTReadingItem, EpistleItem, GospelItem as separate
   classes, or ReadingItem with a `reading_type`? The user specified "readings ('Old
   Testament reading', 'Epistle', 'Gospel')" as types - so maybe model them explicitly.
4. Similarly for music - "music – where 'music' itself is an abstract class of 'hymn' or
   'anthem'" - so Hymn and Anthem as separate item classes (or subclasses of Music item
   base).
5. Any specific fields needed beyond what we have now?
