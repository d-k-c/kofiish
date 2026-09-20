"""Conjugate regular Portuguese ``-er`` verbs."""

from __future__ import annotations

import copy

from kofiish.transformation import conjugated_form_note
from kofiish.verb import Verb


ENDING_RULES = {
    "presente_indicativo": ("stem", {"1sg": "o", "2sg": "es", "3sg": "e", "1pl": "emos", "2pl": "eis", "3pl": "em"}),
    "preterito_perfeito_indicativo": ("stem", {"1sg": "i", "2sg": "este", "3sg": "eu", "1pl": "emos", "2pl": "estes", "3pl": "eram"}),
    "preterito_imperfeito_indicativo": ("stem", {"1sg": "ia", "2sg": "ias", "3sg": "ia", "1pl": "íamos", "2pl": "íeis", "3pl": "iam"}),
    "futuro_indicativo": ("lemma", {"1sg": "ei", "2sg": "ás", "3sg": "á", "1pl": "emos", "2pl": "eis", "3pl": "ão"}),
    "condicional": ("lemma", {"1sg": "ia", "2sg": "ias", "3sg": "ia", "1pl": "íamos", "2pl": "íeis", "3pl": "iam"}),
    "presente_conjuntivo": ("stem", {"1sg": "a", "2sg": "as", "3sg": "a", "1pl": "amos", "2pl": "ais", "3pl": "am"}),
    "preterito_imperfeito_conjuntivo": ("stem", {"1sg": "esse", "2sg": "esses", "3sg": "esse", "1pl": "êssemos", "2pl": "êsseis", "3pl": "essem"}),
    "futuro_conjuntivo": ("stem", {"1sg": "er", "2sg": "eres", "3sg": "er", "1pl": "ermos", "2pl": "erdes", "3pl": "erem"}),
    "imperativo_afirmativo": ("stem", {"2sg": "e", "3sg": "a", "1pl": "amos", "2pl": "ei", "3pl": "am"}),
    "imperativo_negativo": ("stem", {"2sg": "as", "3sg": "a", "1pl": "amos", "2pl": "ais", "3pl": "am"}),
    "infinitivo_pessoal": ("stem", {"1sg": "er", "2sg": "eres", "3sg": "er", "1pl": "ermos", "2pl": "erdes", "3pl": "erem"}),
    "gerundio": ("stem", {"all": "endo"}),
    "participio_passado": ("stem", {"all": "ido"}),
}

# -cer/-ger/-guer verbs soften their stem's final consonant before an ending
# that starts with "a" or "o", to keep the consonant's sound (c/g would
# otherwise harden before a/o, and "gu" would be pronounced /gw/):
# parecer -> pareço/pareça, proteger -> protejo/proteja,
# erguer -> ergo/erga. The mirror image of conjugator_ar's HARDENING.
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
            note = conjugated_form_note(form, generated, ending, "-er", **kwargs)
            if note:
                result.setdefault(tense_name, {})[person] = note

    return result
