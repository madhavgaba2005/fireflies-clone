"""Deterministic, dependency-free summarizer. Every heuristic is simple enough to explain:

* keywords  — most frequent meaningful words (stop-words, numbers and names removed)
* chapters  — the transcript split into equal runs of segments, titled by each run's own keywords
* overview  — who met, what the chapters covered, and the most informative sentence
* actions   — commitment phrases: "I'll …", "<Name>, can you …", "we need to … by Friday"

Same input → same output, so tests are exact and the demo needs no API key.
"""

import re
from collections import Counter
from collections.abc import Sequence

from app.events.payloads import (
    ActionItemPayload,
    ProcessingRequestPayload,
    SegmentPayload,
    SummaryGeneratedPayload,
    TopicPayload,
)
from app.providers.base import ProviderError

MAX_KEYWORDS = 6
MAX_CHAPTERS = 5
SEGMENTS_PER_CHAPTER = 6
MAX_ACTION_ITEMS = 8

STOP_WORDS = frozenset(
    """
    a about above actually after again against all also am an and any are aren't around as at
    back be because been before being below between both but by can can't could couldn't did
    didn't do does doesn't doing don't down during each even every few first for from further
    get gets getting go going good got great had hadn't has hasn't have haven't having he he'd
    he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in
    into is isn't it it's its itself just know last let let's like little look looks lot lots
    make makes many maybe me more most much must my myself need needs next no nor not now of off
    okay on once one only or other ought our ours ourselves out over own pretty probably quite
    rather really right same say says see seems shall she she'd she'll she's should shouldn't so
    some something still such sure take than thank thanks that that's the their theirs them
    themselves then there there's these they they'd they'll they're they've thing things think
    this those though through to today too two under until up us very want wants was wasn't way
    we we'd we'll we're we've well were weren't what what's when when's where where's which
    while who who's whom why why's will with won't would wouldn't yeah yes yet you you'd you'll
    you're you've your yours yourself yourselves actually everyone anything
    """.split()  # noqa: SIM905 — a word block is easier to read and edit than a list
)

# Words that are frequent in speech but never a topic: numbers, fillers, vague nouns.
NOISE_WORDS = frozenset(
    """
    three four five six seven eight nine eleven twelve twenty thirty forty fifty hundred thousand
    million percent second seconds minute minutes hour hours days weeks month months quarter
    exactly honestly mostly quick quickly simple real fine idea question point part side kind
    sort ones everything nothing someone people meeting call team item items start started
    send sent tell told asked said talk
    """.split()  # noqa: SIM905
)
# First verbs of commitments that aren't real tasks ("I'll explain…", "can you start with…").
NON_TASK_VERBS = frozenset({"explain", "start", "need", "be", "keep", "try", "think", "not", "say"})
NON_TASK_PHRASES = ("share my screen",)

MIN_SENTENCE_WORDS = 8
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9'’-]*[A-Za-z0-9]")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_TIME_CUE = re.compile(
    r"\b(by|before|until|end of|tomorrow|today|tonight|this week|next week|monday|tuesday|"
    r"wednesday|thursday|friday|eod|asap)\b",
    re.IGNORECASE,
)
_FIRST_PERSON = re.compile(r"\b(?:I'll|I will|I'm going to|I am going to)\s+(.+)", re.IGNORECASE)
_REQUEST = re.compile(r"^(?:([A-Z][a-z]+),\s+)?(?:can|could) you\s+(.+)", re.IGNORECASE)
_TEAM = re.compile(r"\b(?:we need to|we should|we have to|let's)\s+(.+)", re.IGNORECASE)


def _tokens(text: str, ignore: frozenset[str] = frozenset()) -> list[str]:
    words = (w.lower() for w in _WORD.findall(text))
    return [
        w
        for w in words
        if len(w) > 3 and w not in STOP_WORDS and w not in NOISE_WORDS and w not in ignore
    ]


def _name_tokens(request: ProcessingRequestPayload) -> frozenset[str]:
    """Participant names are frequent but are people, not topics."""
    names = [p.name for p in request.participants] + [s.speaker for s in request.segments]
    return frozenset(part.lower() for name in names for part in name.split())


def keywords(
    segments: Sequence[SegmentPayload],
    limit: int = MAX_KEYWORDS,
    ignore: frozenset[str] = frozenset(),
) -> list[str]:
    counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    for token in (t for s in segments for t in _tokens(s.text, ignore)):
        counts[token] += 1
        first_seen.setdefault(token, len(first_seen))
    ranked = sorted(counts, key=lambda word: (-counts[word], first_seen[word]))
    return [word.capitalize() for word in ranked[:limit]]


def _shorten(sentence: str, max_chars: int = 220) -> str:
    return sentence if len(sentence) <= max_chars else sentence[: max_chars - 1].rstrip() + "…"


def best_sentence(segments: Sequence[SegmentPayload], topic_words: Sequence[str]) -> str:
    """The most informative sentence: most topic words, ignoring short replies ("Sure.")."""
    wanted = {w.lower() for w in topic_words}
    sentences = [s for seg in segments for s in _SENTENCE.split(seg.text.strip()) if s]
    substantial = [s for s in sentences if len(s.split()) >= MIN_SENTENCE_WORDS] or sentences
    best = max(substantial, key=lambda s: (sum(t in wanted for t in _tokens(s)), len(s.split())))
    return _shorten(best)


def chapters(
    segments: Sequence[SegmentPayload], ignore: frozenset[str] = frozenset()
) -> list[TopicPayload]:
    count = max(1, min(MAX_CHAPTERS, round(len(segments) / SEGMENTS_PER_CHAPTER)))
    size = -(-len(segments) // count)  # ceiling division
    topics: list[TopicPayload] = []
    for index in range(0, len(segments), size):
        run = segments[index : index + size]
        words = keywords(run, 2, ignore)
        title = " and ".join(words) if words else f"Part {len(topics) + 1}"
        topics.append(
            TopicPayload(
                title=title[:200], summary=best_sentence(run, words), start_ms=run[0].start_ms
            )
        )
    return topics


def overview(
    request: ProcessingRequestPayload, topics: Sequence[TopicPayload], top_words: Sequence[str]
) -> str:
    speakers = list(dict.fromkeys(s.speaker for s in request.segments))
    names = ", ".join(speakers[:-1]) + f" and {speakers[-1]}" if len(speakers) > 1 else speakers[0]
    covered = "; ".join(t.title.lower() for t in topics)
    return (
        f"{names} met for “{request.title}”. The discussion covered {covered}. "
        f"Key point: {best_sentence(request.segments, top_words)}"
    )


def _clean_task(text: str) -> str:
    task = re.split(r"[.!?]", text, maxsplit=1)[0].strip(" ,;:")
    task = re.sub(r"^(?:also|probably|then|just)\s+", "", task, flags=re.IGNORECASE)
    return task[:1].upper() + task[1:500]


def action_items(request: ProcessingRequestPayload) -> list[ActionItemPayload]:
    first_names = {p.name.split()[0].lower(): p.id for p in request.participants}
    items: list[ActionItemPayload] = []
    seen: set[str] = set()
    for segment in request.segments:
        for sentence in _SENTENCE.split(segment.text):
            assignee: int | None = None
            task: str | None = None
            if match := _FIRST_PERSON.search(sentence):
                task, assignee = match.group(1), segment.speaker_id
            elif match := _REQUEST.search(sentence):
                task = match.group(2)
                assignee = first_names.get((match.group(1) or "").lower())
            elif (match := _TEAM.search(sentence)) and _TIME_CUE.search(sentence):
                task = match.group(1)
            if not task:
                continue
            title = _clean_task(task)
            words = title.split()
            if not 3 <= len(words) <= 25 or words[0].lower() in NON_TASK_VERBS:
                continue
            if title.lower().startswith(NON_TASK_PHRASES):
                continue
            if title.lower() in seen:
                continue
            seen.add(title.lower())
            items.append(
                ActionItemPayload(
                    title=title, assignee_speaker_id=assignee, start_ms=segment.start_ms
                )
            )
            if len(items) == MAX_ACTION_ITEMS:
                return items
    return items


class MockSummaryProvider:
    name = "mock"

    def generate(self, request: ProcessingRequestPayload) -> SummaryGeneratedPayload:
        segments = [s for s in request.segments if s.text.strip()]
        if not segments:
            raise ProviderError("The transcript is empty", retryable=False)
        request = request.model_copy(update={"segments": segments})
        names = _name_tokens(request)
        top_words = keywords(segments, ignore=names)
        topics = chapters(segments, names)
        return SummaryGeneratedPayload(
            meeting_id=request.meeting_id,
            transcript_revision=request.transcript_revision,
            provider=self.name,
            overview=overview(request, topics, top_words),
            keywords=top_words,
            topics=topics,
            action_items=action_items(request),
        )
