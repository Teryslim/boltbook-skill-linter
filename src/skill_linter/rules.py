"""Lint rules. Each rule yields RuleViolation instances over a file's text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True)
class RuleViolation:
    code: str
    msg: str
    path: Path
    line: int


class Rule:
    code: str
    description: str

    def check(self, path: Path, text: str) -> Iterator[RuleViolation]:
        raise NotImplementedError


class R001NoRasterImageEmbed(Rule):
    code = "R001"
    description = "No raster image embeds (Council #617 consensus)"
    _pat = re.compile(
        r"!\[[^\]]*\]\([^)]+\.(?:png|jpg|jpeg|gif|webp|bmp|tiff)(?:\?[^)]*)?\)",
        re.IGNORECASE,
    )

    def check(self, path, text):
        for m in self._pat.finditer(text):
            line = text[: m.start()].count("\n") + 1
            yield RuleViolation(self.code,
                                f"raster image embed forbidden: {m.group(0)[:60]}",
                                path, line)


class R002MermaidNeedsFallback(Rule):
    code = "R002"
    description = "Mermaid block must be preceded by ≥1 line of plain prose (≤3 lines above)"

    def check(self, path, text):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("```mermaid"):
                preceding = [
                    ln.strip() for ln in lines[max(0, i - 3) : i] if ln.strip()
                ]
                # If no preceding non-empty non-heading non-fence line, fail
                useful = [
                    ln for ln in preceding
                    if not ln.startswith("#") and not ln.startswith("```")
                ]
                if not useful:
                    yield RuleViolation(self.code,
                                        "mermaid block has no text-fallback in 3 lines above",
                                        path, i + 1)


class R003NoSecrets(Rule):
    code = "R003"
    description = "No leaked credentials / API keys / personal tokens"
    _patterns = [
        (re.compile(r"sk-[a-zA-Z0-9]{32,}"), "OpenAI-style key"),
        (re.compile(r"ghp_[a-zA-Z0-9]{20,}"), "GitHub PAT (classic)"),
        (re.compile(r"github_pat_[a-zA-Z0-9_]{50,}"), "GitHub PAT (fine-grained)"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
        (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
         "private SSH/RSA key"),
    ]

    def check(self, path, text):
        for pat, name in self._patterns:
            for m in pat.finditer(text):
                line = text[: m.start()].count("\n") + 1
                yield RuleViolation(self.code, f"possible {name} leak", path, line)


class R004HasHarness(Rule):
    code = "R004"
    description = "Skill must declare `harness:` (case-insensitive) within first 20 lines"
    _pat = re.compile(r"^\s*(?:-\s*)?harness\s*[:=]", re.MULTILINE | re.IGNORECASE)

    def check(self, path, text):
        head = "\n".join(text.splitlines()[:20])
        if not self._pat.search(head):
            yield RuleViolation(self.code,
                                "missing `harness:` declaration in first 20 lines",
                                path, 1)


ALL_RULES: list[Rule] = [
    R001NoRasterImageEmbed(),
    R002MermaidNeedsFallback(),
    R003NoSecrets(),
    R004HasHarness(),
]
