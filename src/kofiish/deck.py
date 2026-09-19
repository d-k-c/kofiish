from dataclasses import dataclass, field
from pathlib import Path

import yaml

from kofiish.verb import Verb, VerbYamlLoader


@dataclass(frozen=True)
class ModelMetadata:
    id: int
    name: str


@dataclass(frozen=True)
class DeckMetadata:
    id: int
    name: str


@dataclass(frozen=True)
class Metadata:
    model: ModelMetadata
    deck: DeckMetadata


@dataclass(frozen=True)
class Pronoun:
    prompt: str
    tag: str | None = None

    def get_tag(self):
        return self.tag if self.tag else self.prompt


@dataclass(frozen=True)
class Tense:
    forms: tuple[str, ...]
    cue: str | None


@dataclass
class Deck:
    metadata: Metadata
    fields: tuple[str, ...]
    pronouns: dict[str, Pronoun]
    tenses: dict[str, Tense]
    verbs: dict[str, Verb] = field(default_factory=dict)

    def load_verb(self, verb_path: Path) -> None:
        verb = VerbYamlLoader().load(verb_path)
        self.verbs[verb.lemma] = verb

    def load_verbs(self, verbs_dir: Path) -> None:
        for path in sorted(verbs_dir.iterdir()):
            self.load_verb(path)


class DeckLoader:
    def load(self, path: Path) -> Deck:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return Deck(
            metadata=self._load_metadata(data["metadata"]),
            fields=tuple(data["fields"]),
            pronouns=self._load_pronouns(data["pronouns"]),
            tenses=self._load_tenses(data["tenses"]),
        )

    def _load_metadata(self, data: dict) -> Metadata:
        return Metadata(
            model=ModelMetadata(
                id=data["model"]["id"],
                name=data["model"]["name"],
            ),
            deck=DeckMetadata(
                id=data["deck"]["id"],
                name=data["deck"]["name"],
            ),
        )

    def _load_pronouns(self, data: dict) -> dict[str, Pronoun]:
        return {
            key: Pronoun(
                prompt=value["prompt"],
                tag=value.get("tag"),
            )
            for key, value in data.items()
        }

    def _load_tenses(self, data: dict) -> dict[str, Tense]:
        return {
            key: Tense(
                forms=tuple(value["forms"]),
                cue=value.get("cue", None),
            )
            for key, value in data.items()
        }

