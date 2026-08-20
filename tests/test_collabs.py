"""Offline tests for the collaboration extractor. No network, no raw data."""

import pandas as pd

from src.features.collabs import (
    ALIASES,
    extract_refs,
    load_labels,
    name_hits,
    resolve_to_cohort,
    video_collaborators,
)

ZERKAA = "UChntGq8THlUokhc1tT-M2wA"  # first name "josh", nickname "zerk"
W2S = "UCjtLOfx1yt1NlnFIDyAX3Ug"     # "harry", "wroetoshaw"

# A real cohort handle map, trimmed to the channels used below.
HMAP = {"ksi": "UCksi", "miniminter": "UCmm", "chunkz": "UCchunkz"}
COHORT = set(HMAP.values()) | {"UCother"}


def test_extract_channel_link():
    refs = extract_refs("new vid https://www.youtube.com/channel/UCGmnsW623G1r-Chmo5RB4Yw yo")
    assert refs == {"id:UCGmnsW623G1r-Chmo5RB4Yw"}


def test_extract_handle_forms():
    # /@handle, legacy /c/ and /user/, and a bare @mention all normalise to handles.
    text = ("youtube.com/@KSIplus youtube.com/c/MM7Games youtube.com/user/OldName "
            "shout to @Chunkz")
    assert extract_refs(text) == {
        "handle:ksiplus", "handle:mm7games", "handle:oldname", "handle:chunkz",
    }


def test_bare_handle_keeps_dotted_token_distinct():
    # "@ksi.irl" is a tiktok handle; it must not collapse to the cohort handle "ksi".
    refs = extract_refs("clips on @ksi.irl and main @ksi")
    assert "handle:ksi" in refs
    assert "handle:ksi.irl" in refs


def test_extract_ignores_non_youtube_and_email():
    text = "mail me a@b.com follow twitter.com/miniminter and instagram @notachannel_x"
    refs = extract_refs(text)
    # No youtube channel link or /@ handle here, and the email local part is not an @mention.
    assert "id:" not in " ".join(refs)
    assert "handle:b.com" not in refs  # email domain, not a mention


def test_resolve_restricts_to_cohort():
    refs = {"id:UCksi", "id:UCstranger", "handle:chunkz", "handle:randomsponsor"}
    assert resolve_to_cohort(refs, HMAP, COHORT) == {"UCksi", "UCchunkz"}


def test_video_collaborators_excludes_self():
    title = "race against Chunkz"
    desc = "follow @ksi and my own @miniminter here youtube.com/@Chunkz"
    got = video_collaborators(title, desc, HMAP, COHORT, own_id="UCmm")
    assert got == {"UCksi", "UCchunkz"}  # own channel UCmm dropped


def test_name_hits_matches_first_name_word_bounded():
    # "JOSH (Zerkaa)" is the roster-footer form; the first name resolves to Zerkaa.
    assert name_hits("? JOSH (Zerkaa)") == {ZERKAA}
    # Word-bounded: a longer token that merely contains the alias must not match.
    assert name_hits("joshua reviews the game") == set()


def test_video_collaborators_picks_up_member_name():
    # No links here; the collaborator is recoverable only from the member name.
    cohort = set(ALIASES) | {"UCother"}
    got = video_collaborators("SIDEMEN CHALLENGE", "? HARRY (W2S)\n? JOSH (Zerkaa)",
                              {}, cohort, own_id=ZERKAA)
    assert got == {W2S}  # own channel Zerkaa dropped even though named


def test_load_labels_roundtrip(tmp_path):
    p = tmp_path / "labels.csv"
    pd.DataFrame(
        [{"video_id": "v1", "collaborator_channel_ids": "UCa;UCb", "hand_checked": "1"},
         {"video_id": "v2", "collaborator_channel_ids": "", "hand_checked": "1"}]
    ).to_csv(p, index=False)
    labels = load_labels(p)
    assert labels == {"v1": {"UCa", "UCb"}, "v2": set()}
