from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

import yaml


# Morphology is deliberately independent of YAML, deck configuration, and
# rendering. A tense maps a person (for example ``"1sg"``) to its form.
Tense: TypeAlias = dict[str, str | None]
Verb: TypeAlias = dict[str, Tense]


@dataclass
class Context:
    cue: str | None
    hint: str | None = None


@dataclass
class VerbDefinition:
    """Sparse verb data authored in a verb YAML file."""

    lemma: str
    translation: str
    transformations: tuple[str, ...]
    forms: Verb = field(default_factory=dict)
    contexts: dict[str, dict[str, Context]] = field(default_factory=dict)
    analogs: dict[str, Verb] = field(default_factory=dict)
    notes: dict[str, dict[str, str]] = field(default_factory=dict)
    # One note per tense, shown on every card of that tense: a pattern
    # shared by all its forms, e.g. an irregular stem.
    patterns: dict[str, str] = field(default_factory=dict)


@dataclass
class ResolvedVerb:
    """A verb ready for card generation after morphology and overrides merge."""

    lemma: str
    translation: str
    forms: Verb
    contexts: dict[str, dict[str, Context]]
    analogs: dict[str, Verb] = field(default_factory=dict)
    notes: dict[str, dict[str, str]] = field(default_factory=dict)

    def get_context(self, tense_name: str, person: str) -> Context:
        tense_contexts = self.contexts[tense_name]
        return tense_contexts.get(person, tense_contexts["default"])

    def get_note(self, tense_name: str, person: str) -> str | None:
        return self.notes.get(tense_name, {}).get(person)


class VerbDefinitionYamlLoader:
    def load(self, path: str | Path) -> VerbDefinition:
        path = Path(path)

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        metadata = data["metadata"]
        return VerbDefinition(
            lemma=metadata["lemma"],
            translation=metadata["translation"],
            transformations=tuple(data.get("transformations", ())),
            forms=self._load_forms(data.get("tenses", {})),
            contexts=self._load_contexts(data.get("tenses", {})),
            analogs=self._load_analogs(data.get("analogs") or {}),
            notes=self._load_notes(data.get("tenses", {})),
            patterns=self._load_patterns(data.get("tenses", {})),
        )

    @staticmethod
    def _load_forms(tenses: dict) -> Verb:
        return {
            tense_name: dict(tense_data.get("forms", {}))
            for tense_name, tense_data in tenses.items()
        }

    @staticmethod
    def _load_contexts(tenses: dict) -> dict[str, dict[str, Context]]:
        return {
            tense_name: {
                context_key: Context(
                    cue=context_data.get("cue"),
                    hint=context_data.get("hint"),
                )
                for context_key, context_data in tense_data.get("context", {}).items()
            }
            for tense_name, tense_data in tenses.items()
        }

    @staticmethod
    def _load_notes(tenses: dict) -> dict[str, dict[str, str]]:
        return {
            tense_name: dict(tense_data.get("notes", {}))
            for tense_name, tense_data in tenses.items()
        }

    @staticmethod
    def _load_patterns(tenses: dict) -> dict[str, str]:
        return {
            tense_name: tense_data["pattern"]
            for tense_name, tense_data in tenses.items()
            if tense_data.get("pattern")
        }

    def _load_analogs(self, analogs: dict) -> dict[str, Verb]:
        return {
            lemma: self._load_forms(tenses)
            for lemma, tenses in analogs.items()
        }
