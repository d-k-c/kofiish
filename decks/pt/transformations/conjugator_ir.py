"""Conjugate regular Portuguese ``-ir`` verbs."""

from __future__ import annotations

import copy

from kofiish.transformation import conjugated_form_note
from kofiish.verb import Verb


ENDING_RULES = {
    "presente_indicativo": ("stem", {"1sg": "o", "2sg": "es", "3sg": "e", "1pl": "imos", "2pl": "is", "3pl": "em"}),
    "preterito_perfeito_indicativo": ("stem", {"1sg": "i", "2sg": "iste", "3sg": "iu", "1pl": "imos", "2pl": "istes", "3pl": "iram"}),
    "preterito_imperfeito_indicativo": ("stem", {"1sg": "ia", "2sg": "ias", "3sg": "ia", "1pl": "íamos", "2pl": "íeis", "3pl": "iam"}),
    "futuro_indicativo": ("lemma", {"1sg": "ei", "2sg": "ás", "3sg": "á", "1pl": "emos", "2pl": "eis", "3pl": "ão"}),
    "condicional": ("lemma", {"1sg": "ia", "2sg": "ias", "3sg": "ia", "1pl": "íamos", "2pl": "íeis", "3pl": "iam"}),
    "presente_conjuntivo": ("stem", {"1sg": "a", "2sg": "as", "3sg": "a", "1pl": "amos", "2pl": "ais", "3pl": "am"}),
    "preterito_imperfeito_conjuntivo": ("stem", {"1sg": "isse", "2sg": "isses", "3sg": "isse", "1pl": "íssemos", "2pl": "ísseis", "3pl": "issem"}),
    "futuro_conjuntivo": ("stem", {"1sg": "ir", "2sg": "ires", "3sg": "ir", "1pl": "irmos", "2pl": "irdes", "3pl": "irem"}),
    "imperativo_afirmativo": ("stem", {"2sg": "e", "3sg": "a", "1pl": "amos", "2pl": "i", "3pl": "am"}),
    "imperativo_negativo": ("stem", {"2sg": "as", "3sg": "a", "1pl": "amos", "2pl": "ais", "3pl": "am"}),
    "infinitivo_pessoal": ("stem", {"1sg": "ir", "2sg": "ires", "3sg": "ir", "1pl": "irmos", "2pl": "irdes", "3pl": "irem"}),
    "gerundio": ("stem", {"all": "indo"}),
    "participio_passado": ("stem", {"all": "ido"}),
}

# -cir/-gir/-guir verbs soften their stem's final consonant before an ending
# that starts with "a" or "o", to keep the consonant's sound (c/g would
# otherwise harden before a/o, and "gu" would be pronounced /gw/):
# ressarcir -> ressarço/ressarça, exigir -> exijo/exija,
# distinguir -> distingo/distinga. Same rule as conjugator_er's SOFTENING.
SOFTENING = {"gu": "g", "c": "ç", "g": "j"}


def _softening(stem: str) -> tuple[str, str] | None:
    for suffix, replacement in SOFTENING.items():
        if stem.endswith(suffix):
            return suffix, replacement
    return None


def _softened_stem(stem: str) -> str | None:
    softening = _softening(stem)
    if not softening:
        return None
    suffix, replacement = softening
    return stem[: -len(suffix)] + replacement


def _softens(ending: str) -> bool:
    return ending[0] in "ao"


def transform(lemma: str, verb: Verb) -> Verb:
    verb = copy.deepcopy(verb)
    stem = lemma[:-2]
    softened_stem = _softened_stem(stem)

    for tense_name, (base, endings) in ENDING_RULES.items():
        verb[tense_name].update(
            {
                person: (
                    lemma if base == "lemma"
                    else softened_stem if softened_stem and _softens(ending)
                    else stem
                ) + ending
                for person, ending in endings.items()
            }
        )

    return verb


def notes(lemma: str, forms: Verb | None = None) -> dict[str, dict[str, str]]:
    stem = lemma[:-2]
    softening = _softening(stem)
    softened_stem = _softened_stem(stem)

    result: dict[str, dict[str, str]] = {}
    for tense_name, (base, endings) in ENDING_RULES.items():
        for person, ending in endings.items():
            if base == "lemma":
                generated, kwargs = lemma + ending, {"on_infinitive": True}
            elif softening and _softens(ending):
                generated, kwargs = softened_stem + ending, {"spelling_change": softening}
            else:
                generated, kwargs = stem + ending, {}
            form = generated if forms is None else forms.get(tense_name, {}).get(person)
            note = conjugated_form_note(form, generated, ending, "-ir", **kwargs)
            if note:
                result.setdefault(tense_name, {})[person] = note

    return result
