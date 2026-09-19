import yaml

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Optional

class Person(StrEnum):

    FIRST_SINGULAR  = "1sg"
    SECOND_SINGULAR = "2sg"
    THIRD_SINGULAR  = "3sg"
    FIRST_PLUPAL    = "1pl"
    SECOND_PLUPAL   = "2pl"
    THIRD_PLUPAL    = "3pl"
    ALL             = "all"

@dataclass
class Context:
    cue: str
    hint: Optional[str] = None


class Form:

    def __init__(self, tense, person, form):
        self.tense = tense
        self.person = person
        self.form = form

    @property
    def context(self):
        return self.tense.get_context(self.person)

    @property
    def analogs(self):
        return self.tense.get_analogs(self.person)

    def __repr__(self):
        attr = ["person", "form", "context", "analogs"]

        rep = ", ".join(["'{0}': {1}".format(a, getattr(self, a)) for a in attr])

        return "<Form (" + rep + ")>"

@dataclass
class Tense:
    verb: "Verb"
    tense: str
    forms: dict[str, Form] = field(default_factory=dict)
    contexes: dict[str, Context] = field(default_factory=dict)

    def __getitem__(self, key):
        try:
            p = Person(key)
        except ValueError:
            raise KeyError(f"Invalid key for Tense dictionary: {key}")

        if key not in self.forms:
            self.forms[key] = Form(self, key, None)

        return self.forms[key]


    def get_context(self, person):
        key = person if person in self.contexes else "default"

        return self.contexes[key]

    def get_analogs(self, person):
        result = []

        for a in self.verb.analogs:
            if not self.tense in a.tenses:
                continue

            t = a.tenses[self.tense]
            if not person in t.forms:
                continue

            result.append((a.lemma, t[person]))

        return result

@dataclass
class Verb:
    lemma: str
    translation: str = field(default_factory=str)
    conjugation_type: str = field(default_factory=str)

    tenses: dict[str, Tense] = field(default_factory=dict)
    analogs: list["Verb"] = field(default_factory=list)

class VerbYamlLoader:

    def load(self, path: str | Path):
        path = Path(path)

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        metadata = data["metadata"]
        conjugation = data["conjugation"]

        verb = Verb(
            lemma=metadata["lemma"],
            translation=metadata["translation"],
            conjugation_type=conjugation["type"],
        )

        for tense_name, tense_data in data.get("tenses", {}).items():
            tense = Tense(verb, tense_name)

            tense.contexes = dict()
            for ctx_key, ctx_data in tense_data.get("context").items():
                ctx = Context(
                        cue=ctx_data.get("cue"),
                        hint=ctx_data.get("hint"))
                tense.contexes[ctx_key] = ctx

            for person, form in tense_data.get("forms", {}).items():
                f = Form(tense, person, form)
                tense.forms[person] = f

            verb.tenses[tense_name] = tense

        for lemma, analog_data in data.get("analogs", {}).items():
            analog = Verb(lemma=lemma)

            for tense_name, tense_data in analog_data.items():
                tense = Tense(analog, tense_name)

                for person, form in tense_data.get("forms", {}).items():
                    tense.forms[person] = form

                analog.tenses[tense_name] = tense

            verb.analogs.append(analog)

        return verb
