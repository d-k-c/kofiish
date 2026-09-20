import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from kofiish.verb import VerbDefinition, VerbDefinitionYamlLoader


@dataclass(frozen=True)
class ModelMetadata:
    id: int
    name: str


@dataclass(frozen=True)
class DeckMetadata:
    id: int
    name: str


@dataclass(frozen=True)
class DeckOptions:
    """An Anki options preset shipped with the deck.

    Steps are in minutes and the maximum interval in days, as in Anki's
    deck options screen.
    """
    id: int
    name: str
    new_per_day: int
    reviews_per_day: int
    learning_steps: tuple[int, ...]
    new_card_order: str  # "sequential" or "random"
    relearning_steps: tuple[int, ...]
    leech_threshold: int
    maximum_interval: int
    desired_retention: float

    NEW_CARD_ORDERS = ("random", "sequential")  # index is Anki's new.order value


@dataclass(frozen=True)
class Metadata:
    model: ModelMetadata
    deck: DeckMetadata
    language: str
    options: DeckOptions | None = None


@dataclass(frozen=True)
class Pronoun:
    prompt: str
    tag: str | None = None

    def get_tag(self):
        return self.tag if self.tag else self.prompt


@dataclass(frozen=True)
class DeckTenseCfg:
    forms: tuple[str, ...]
    cue: str | None
    pronoun_hint: bool = False
    pronoun_overrides: dict[str, str] = field(default_factory=dict)

    def pronoun_for(self, form_name: str, pronouns: dict[str, Pronoun]) -> str | None:
        return self.pronoun_overrides.get(form_name, pronouns[form_name].prompt)


@dataclass
class Deck:
    metadata: Metadata
    fields: tuple[str, ...]
    pronouns: dict[str, Pronoun]
    tense_cfgs: dict[str, DeckTenseCfg]
    verb_order: tuple[str, ...]

    def load_verbs(self, verbs_dir: Path) -> dict[str, VerbDefinition]:
        loader = VerbDefinitionYamlLoader()
        verbs = {}
        for path in sorted(verbs_dir.iterdir()):
            verb = loader.load(path)
            verbs[verb.lemma] = verb

        missing = set(self.verb_order) - set(verbs)
        for lemma in sorted(missing):
            print(f"warning: {lemma!r} is listed in deck.yaml but has no verb file yet, skipping", file=sys.stderr)

        # A verb file that isn't in verb_order is treated as shelved, not an
        # error: keeping a verb's file around without it being active in the
        # deck (e.g. to re-add later) is a valid, intentional state. A verb
        # in verb_order with no file yet (not yet authored) is symmetric:
        # skipped with a warning, not a hard error, so the deck still
        # builds while it's being filled in incrementally.

        return {lemma: verbs[lemma] for lemma in self.verb_order if lemma in verbs}


class DeckLoader:
    def load(self, path: Path) -> Deck:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return Deck(
            metadata=self._load_metadata(data["metadata"]),
            fields=tuple(data["fields"]),
            pronouns=self._load_pronouns(data["pronouns"]),
            tense_cfgs=self._load_tenses(data["tenses"]),
            verb_order=tuple(data["verbs"]),
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
            language=data["language"],
            options=self._load_options(data["options"]) if "options" in data else None,
        )

    def _load_options(self, data: dict) -> DeckOptions:
        options = DeckOptions(
            **{
                key: tuple(value) if isinstance(value, list) else value
                for key, value in data.items()
            }
        )
        if options.new_card_order not in DeckOptions.NEW_CARD_ORDERS:
            raise ValueError(
                f"new_card_order must be one of {', '.join(DeckOptions.NEW_CARD_ORDERS)}: "
                f"{options.new_card_order}"
            )
        return options

    def _load_pronouns(self, data: dict) -> dict[str, Pronoun]:
        return {
            key: Pronoun(
                prompt=value["prompt"],
                tag=value.get("tag"),
            )
            for key, value in data.items()
        }

    def _load_tenses(self, data: dict) -> dict[str, DeckTenseCfg]:
        return {
            key: DeckTenseCfg(
                forms=tuple(value["forms"]),
                cue=value.get("cue", None),
                pronoun_hint=value.get("pronoun_hint", False),
                pronoun_overrides=dict(value.get("pronouns", {})),
            )
            for key, value in data.items()
        }
