"""Parse ISO 8601 durations and split long-form from shorts.

YouTube returns contentDetails.duration as ISO 8601 (PT2H13M22S). pandas parses
that form directly, so no isodate dependency and no hand-written regex.

The threshold is passed in from config/params.yaml by the caller, never inlined.
A video at or below the threshold is a short (params.yaml), so long-form is a
strict greater-than.
"""

import pandas as pd


def parse_duration_seconds(duration):
    """ISO 8601 duration Series to float seconds. Unparseable values become NaN
    (livestream placeholders like P0D parse to 0; empty strings become NaN)."""
    return pd.to_timedelta(duration, errors="coerce").dt.total_seconds()


def long_form_mask(seconds, threshold_seconds):
    """True where a video is long-form. NaN durations are not long-form."""
    return seconds > threshold_seconds
