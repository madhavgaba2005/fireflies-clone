import json

import pytest

from app.services.transcript_parser import (
    MAX_SEGMENTS,
    UNKNOWN_SPEAKER,
    ParsedSegment,
    TranscriptParseError,
    parse_transcript,
)

# --- txt ------------------------------------------------------------------------------------


def test_txt_lines_become_segments_ending_where_the_next_starts() -> None:
    segments = parse_transcript(
        "[00:00] John: Let's begin today's meeting.\n"
        "[00:18] Sarah Chen: The launch is scheduled for November.\n"
        "[00:42] John: We need to finalize the API."
    )
    assert segments[0] == ParsedSegment("John", 0, 18_000, "Let's begin today's meeting.")
    assert segments[1] == ParsedSegment(
        "Sarah Chen", 18_000, 42_000, "The launch is scheduled for November."
    )
    # last segment: estimated from words (6 words × 400 ms = 2.4 s)
    assert segments[2].start_ms == 42_000 and segments[2].end_ms == 44_400


def test_txt_accepts_hours_brackets_optional_and_continuation_lines() -> None:
    segments = parse_transcript(
        "1:02:03 Priya: First part\n  of a long sentence.\n\n[01:02:10] Arjun: Reply"
    )
    assert segments[0].start_ms == 3_723_000
    assert segments[0].text == "First part of a long sentence."
    assert segments[1].start_ms == 3_730_000


def test_txt_short_last_segment_gets_minimum_duration() -> None:
    (segment,) = parse_transcript("[00:05] A: Hi")
    assert segment.end_ms - segment.start_ms == 2000


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "empty"),
        ("   \n  ", "empty"),
        ("no timestamp here", "Line 1"),
        ("[00:10] A: later\n[00:05] B: earlier", "Line 2: Timestamps must not go backwards"),
        ("[00:75] A: bad seconds", "Invalid timestamp"),
        ("[1:75:00] A: bad minutes", "Invalid timestamp"),
    ],
)
def test_txt_errors_are_reported_with_line_numbers(text: str, message: str) -> None:
    with pytest.raises(TranscriptParseError, match=message):
        parse_transcript(text)


def test_too_many_segments_is_rejected() -> None:
    text = "\n".join(f"[{i // 60:02d}:{i % 60:02d}] A: x" for i in range(MAX_SEGMENTS + 1))
    with pytest.raises(TranscriptParseError, match="more than"):
        parse_transcript(text)


# --- vtt ------------------------------------------------------------------------------------

VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.500
<v Priya Sharma>Welcome everyone.</v>

2
00:00:05.000 --> 00:00:09.000
Arjun: Thanks. Let's look
at the <b>release</b>.

00:00:10,000 --> 00:00:12,000
No speaker on this cue.
"""


def test_vtt_reads_voice_tags_prefixes_and_multi_line_cues() -> None:
    segments = parse_transcript(VTT, "vtt")
    assert segments == [
        ParsedSegment("Priya Sharma", 1000, 4500, "Welcome everyone."),
        ParsedSegment("Arjun", 5000, 9000, "Thanks. Let's look at the release."),
        ParsedSegment(UNKNOWN_SPEAKER, 10_000, 12_000, "No speaker on this cue."),
    ]


def test_vtt_requires_header_and_valid_cues() -> None:
    with pytest.raises(TranscriptParseError, match="WEBVTT"):
        parse_transcript("00:00:01.000 --> 00:00:02.000\nhi", "vtt")
    with pytest.raises(TranscriptParseError, match="ends before it starts"):
        parse_transcript("WEBVTT\n\n00:00:05.000 --> 00:00:02.000\nhi", "vtt")
    with pytest.raises(TranscriptParseError, match="No transcript lines"):
        parse_transcript("WEBVTT\n\nNOTE nothing here", "vtt")


# --- json -----------------------------------------------------------------------------------


def test_json_list_and_wrapped_forms_are_sorted_by_start() -> None:
    data = [
        {"speaker": "B", "start": 5, "text": "second"},
        {"speaker": "A", "start": 0.5, "end": 4.25, "text": "first"},
    ]
    for text in (json.dumps(data), json.dumps({"segments": data})):
        segments = parse_transcript(text, "json")
        assert segments[0] == ParsedSegment("A", 500, 4250, "first")
        assert segments[1].speaker == "B" and segments[1].start_ms == 5000


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("{not json", "Invalid JSON"),
        ('{"other": 1}', "must be a list"),
        ('[{"speaker": "A"}]', "Segment 1 needs"),
        ('[{"start": -1, "text": "x"}]', "invalid times"),
        ('[{"start": 5, "end": 1, "text": "x"}]', "invalid times"),
    ],
)
def test_json_errors(text: str, message: str) -> None:
    with pytest.raises(TranscriptParseError, match=message):
        parse_transcript(text, "json")


def test_json_missing_speaker_uses_placeholder() -> None:
    (segment,) = parse_transcript('[{"start": 0, "text": "hi"}]', "json")
    assert segment.speaker == UNKNOWN_SPEAKER
