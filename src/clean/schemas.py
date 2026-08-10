"""Pandera contracts for the cleaned video and channel tables.

Validation output is a finding, not scaffolding (PROJECT_PLAN 8.4): a row that
fails the schema is a defect in the pull to report, not a case to silently drop.
The schemas run in src/clean/build.py after dtype coercion.

Counts arrive from the API as strings and can be absent (statistics hidden), so
they are nullable Int64 with a non-negative check. video_id and channel_id are
the join keys and must be present.
"""

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

# Text columns use the pandas string dtype, coerced so validation is stable
# whatever dtype read_json produces. Counts are nullable Int64 (statistics can
# be hidden) and must be non-negative.
_count = Column("Int64", Check.ge(0), nullable=True, coerce=True)
_text = lambda nullable=False: Column("string", nullable=nullable, coerce=True)

VIDEO_SCHEMA = DataFrameSchema(
    {
        "video_id": Column("string", nullable=False, unique=True, coerce=True),
        "channel_id": _text(),
        "published_at": Column("datetime64[us, UTC]", nullable=False, coerce=True),
        "duration": _text(),
        "view_count": _count,
        "like_count": _count,
        "title": _text(),
        "description": _text(nullable=True),
    },
    strict=False,  # derived columns (duration_seconds, flags) are added downstream
)

CHANNEL_SCHEMA = DataFrameSchema(
    {
        "channel_id": Column("string", nullable=False, unique=True, coerce=True),
        "title": _text(),
        "published_at": Column("datetime64[us, UTC]", nullable=False, coerce=True),
        "subscriber_count": _count,
        "view_count": _count,
        "video_count": _count,
    },
    strict=False,
)


def validate_videos(df):
    return VIDEO_SCHEMA.validate(df, lazy=True)


def validate_channels(df):
    return CHANNEL_SCHEMA.validate(df, lazy=True)
