"""Turns transcript text into ordered segments. Supported formats: txt, vtt, json.

txt  — one utterance per line:  "[00:18] Sarah Chen: The launch is in November."
       ([h:mm:ss] also accepted; a line without a timestamp continues the previous utterance)
vtt  — WebVTT cues; speaker from a "<v Name>" voice tag or a "Name:" prefix
json — [{"speaker": "...", "start": 12.5, "end": 18.0, "text": "..."}]  (seconds; "end" optional)

A segment ends where the next one starts; the last one gets an estimate from its word count.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

TranscriptFormat = Literal["txt", "vtt", "json"]

MAX_SEGMENTS = 5000
UNKNOWN_SPEAKER = "Unknown speaker"
_MS_PER_WORD = 400  # ≈150 words per minute
_MIN_LAST_SEGMENT_MS = 2000


class TranscriptParseError(ValueError):
    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message if line is None else f"Line {line}: {message}")
        self.line = line


@dataclass(frozen=True)
class ParsedSegment:
    speaker: str
    start_ms: int
    end_ms: int
    text: str


@dataclass
class _Draft:
    speaker: str
    start_ms: int
    text: str
    end_ms: int | None = None


_TIMESTAMP = r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})"
_TXT_LINE = re.compile(rf"^\[?{_TIMESTAMP}\]?\s+([^:\[\]]{{1,100}}?)\s*:\s*(.+)$")
_VTT_TIME = re.compile(
    r"^\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})"
)
_VTT_VOICE = re.compile(r"^<v(?:\.[^\s>]+)*\s+([^>]+)>(.*?)(?:</v>)?$")
_SPEAKER_PREFIX = re.compile(r"^([^:]{1,100}?):\s+(.+)$")
_TAGS = re.compile(r"<[^>]+>")


def parse_transcript(text: str, fmt: TranscriptFormat = "txt") -> list[ParsedSegment]:
    if not text.strip():
        raise TranscriptParseError("Transcript is empty")
    drafts = {"txt": _parse_txt, "vtt": _parse_vtt, "json": _parse_json}[fmt](text)
    if not drafts:
        raise TranscriptParseError("No transcript lines found")
    if len(drafts) > MAX_SEGMENTS:
        raise TranscriptParseError(f"Transcript has more than {MAX_SEGMENTS} segments")
    return _finalize(drafts)


def _to_ms(hours: str | None, minutes: str, seconds: str, millis: str = "0") -> int:
    return ((int(hours or 0) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)


def _parse_txt(text: str) -> list[_Draft]:
    drafts: list[_Draft] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        match = _TXT_LINE.match(line)
        if match:
            hours, minutes, seconds, speaker, body = match.groups()
            if int(seconds) >= 60 or (hours is not None and int(minutes) >= 60):
                raise TranscriptParseError(f"Invalid timestamp in '{line[:40]}'", number)
            start = _to_ms(hours, minutes, seconds)
            if drafts and start < drafts[-1].start_ms:
                raise TranscriptParseError("Timestamps must not go backwards", number)
            drafts.append(_Draft(speaker.strip(), start, body.strip()))
        elif drafts:
            drafts[-1].text += " " + line  # continuation of the previous utterance
        else:
            raise TranscriptParseError(
                "Expected '[mm:ss] Speaker: text' (e.g. '[00:05] Priya: Hello')", number
            )
    return drafts


def _parse_vtt(text: str) -> list[_Draft]:
    lines = text.splitlines()
    if not lines or not lines[0].lstrip("﻿").startswith("WEBVTT"):
        raise TranscriptParseError("WebVTT files must start with 'WEBVTT'", 1)
    drafts: list[_Draft] = []
    index = 1
    while index < len(lines):
        timing = _VTT_TIME.match(lines[index])
        if not timing:
            index += 1
            continue
        groups = timing.groups()
        start, end = _to_ms(*groups[:4]), _to_ms(*groups[4:])
        if end < start:
            raise TranscriptParseError("Cue ends before it starts", index + 1)
        cue_lines: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip():
            cue_lines.append(lines[index].strip())
            index += 1
        cue = " ".join(cue_lines)
        speaker = UNKNOWN_SPEAKER
        voice = _VTT_VOICE.match(cue)
        if voice:
            speaker, cue = voice.group(1).strip(), voice.group(2)
        else:
            prefix = _SPEAKER_PREFIX.match(cue)
            if prefix:
                speaker, cue = prefix.group(1).strip(), prefix.group(2)
        body = _TAGS.sub("", cue).strip()
        if body:
            drafts.append(_Draft(speaker, start, body, end))
    drafts.sort(key=lambda draft: draft.start_ms)
    return drafts


def _parse_json(text: str) -> list[_Draft]:
    try:
        data: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TranscriptParseError(f"Invalid JSON: {exc.msg}", exc.lineno) from exc
    if isinstance(data, dict):
        data = data.get("segments")
    if not isinstance(data, list):
        raise TranscriptParseError('JSON must be a list of segments or {"segments": [...]}')
    drafts: list[_Draft] = []
    for position, item in enumerate(data, start=1):
        try:
            speaker = str(item.get("speaker") or UNKNOWN_SPEAKER).strip()
            start = round(float(item["start"]) * 1000)
            end = round(float(item["end"]) * 1000) if item.get("end") is not None else None
            body = str(item["text"]).strip()
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise TranscriptParseError(
                f"Segment {position} needs 'start' (seconds) and 'text'"
            ) from exc
        if start < 0 or (end is not None and end < start):
            raise TranscriptParseError(f"Segment {position} has invalid times")
        if body:
            drafts.append(_Draft(speaker, start, body, end))
    drafts.sort(key=lambda draft: draft.start_ms)
    return drafts


def _finalize(drafts: list[_Draft]) -> list[ParsedSegment]:
    segments: list[ParsedSegment] = []
    for position, draft in enumerate(drafts):
        if draft.end_ms is not None:
            end = draft.end_ms
        elif position + 1 < len(drafts):
            end = drafts[position + 1].start_ms
        else:
            words = len(draft.text.split())
            end = draft.start_ms + max(_MIN_LAST_SEGMENT_MS, words * _MS_PER_WORD)
        segments.append(
            ParsedSegment(draft.speaker[:100], draft.start_ms, max(end, draft.start_ms), draft.text)
        )
    return segments
