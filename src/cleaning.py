"""Text cleaning helpers for subtitle-derived episode scripts."""

from __future__ import annotations

import math
import re
from collections import Counter

import pandas as pd


_HONORIFIC_PATTERN = re.compile(
    r"(?i)(?<=\w)(?:-|\s+)(?:san|sama|kun|chan|sensei|senpai|sempai|dono|shi)\b"
)
_NUMBER_PATTERN = re.compile(
    r"(?i)\b(?:episode|ep)\s*#?\s*\d+\b"
    r"|\b\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?\b"
    r"|\b\d+\b"
)


def clean_episode_scripts(
    scripts: pd.Series,
    min_repeat_episodes: int = 5,
    min_repeat_fraction: float = 0.05,
    block_lines: int = 3,
) -> pd.Series:
    """Clean subtitle text and remove blocks repeated across episodes.

    Repeated content is detected from consecutive normalized lines and removed
    only when the block occurs in enough distinct episodes. The default
    threshold helps remove recurring openings or songs without discarding
    common single-line dialogue.
    """
    if min_repeat_episodes < 2 or block_lines < 2:
        raise ValueError("min_repeat_episodes and block_lines must be at least 2")
    if not 0 < min_repeat_fraction <= 1:
        raise ValueError("min_repeat_fraction must be in (0, 1]")

    if not isinstance(scripts, pd.Series):
        scripts = pd.Series(scripts)

    def split_and_clean(script: object) -> tuple[list[str], list[str]]:
        text = re.sub(r"\{[^}]*\}|<[^>]+>|\[\s*\d+\s*\]", " ", str(script))
        text = re.sub(r"\\[hH]", " ", text)
        pieces = re.split(r"\\[Nn]|\\n|\\r|[\r\n]+", text)

        cleaned_lines = []
        line_keys = []
        for piece in pieces:
            piece = _HONORIFIC_PATTERN.sub("", piece)
            piece = _NUMBER_PATTERN.sub(" ", piece)
            piece = re.sub(r"\s+", " ", piece).strip()
            key = " ".join(re.sub(r"[^\w\s]", " ", piece.casefold()).split())
            cleaned_lines.append(piece)
            line_keys.append(key)

        return cleaned_lines, line_keys

    parsed_scripts = [
        split_and_clean(script) for script in scripts.fillna("")
    ]
    repeat_threshold = max(
        min_repeat_episodes,
        math.ceil(len(parsed_scripts) * min_repeat_fraction),
    )

    repeated_blocks: Counter[tuple[str, ...]] = Counter()
    for _, line_keys in parsed_scripts:
        blocks = {
            tuple(line_keys[index : index + block_lines])
            for index in range(len(line_keys) - block_lines + 1)
            if all(
                len(key) >= 12
                for key in line_keys[index : index + block_lines]
            )
        }
        repeated_blocks.update(blocks)

    common_blocks = {
        block
        for block, count in repeated_blocks.items()
        if count >= repeat_threshold
    }
    cleaned_scripts = []
    for lines, line_keys in parsed_scripts:
        repeated_line_indexes = set()
        for index in range(len(line_keys) - block_lines + 1):
            block = tuple(line_keys[index : index + block_lines])
            if block in common_blocks:
                repeated_line_indexes.update(range(index, index + block_lines))

        retained_lines = [
            line
            for index, (line, key) in enumerate(zip(lines, line_keys))
            if index not in repeated_line_indexes
            and key
            and not re.search(r"[♪♫♬]", line)
        ]
        cleaned_scripts.append(" ".join(retained_lines))

    return pd.Series(cleaned_scripts, index=scripts.index, name=scripts.name)
