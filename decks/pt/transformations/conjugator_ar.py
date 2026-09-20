"""Conjugate regular Portuguese ``-ar`` verbs."""

from __future__ import annotations

import copy

from kofiish.transformation import conjugated_form_note
from kofiish.verb import Verb


ENDING_RULES = {
    "presente_indicativo": ("stem", {"1sg": "o", "2sg": "as", "3sg": "a", "1pl": "amos", "2pl": "ais", "3pl": "am"}),
    "preterito_perfeito_indicativo": ("stem", {"1sg": "ei", "2sg": "aste", "3sg": "ou", "1pl": "ámos", "2pl": "astes", "3pl": "aram"}),
    "preterito_imperfeito_indicativo": ("stem", {"1sg": "ava", "2sg": "avas", "3sg": "ava", "1pl": "ávamos", "2pl": "áveis", "3pl": "avam"}),
    "futuro_indicativo": ("lemma", {"1sg": "ei", "2sg": "ás", "3sg": "á", "1pl": "emos", "2pl": "eis", "3pl": "ão"}),
    "condicional": ("lemma", {"1sg": "ia", "2sg": "ias", "3sg": "ia", "1pl": "íamos", "2pl": "íeis", "3pl": "iam"}),
    "presente_conjuntivo": ("stem", {"1sg": "e", "2sg": "es", "3sg": "e", "1pl": "emos", "2pl": "eis", "3pl": "em"}),
    "preterito_imperfeito_conjuntivo": ("stem", {"1sg": "asse", "2sg": "asses", "3sg": "asse", "1pl": "ássemos", "2pl": "ásseis", "3pl": "assem"}),
    "futuro_conjuntivo": ("stem", {"1sg": "ar", "2sg": "ares", "3sg": "ar", "1pl": "armos", "2pl": "ardes", "3pl": "arem"}),
    "imperativo_afirmativo": ("stem", {"2sg": "a", "3sg": "e", "1pl": "emos", "2pl": "ai", "3pl": "em"}),
    "imperativo_negativo": ("stem", {"2sg": "es", "3sg": "e", "1pl": "emos", "2pl": "eis", "3pl": "em"}),
    "infinitivo_pessoal": ("stem", {"1sg": "ar", "2sg": "ares", "3sg": "ar", "1pl": "armos", "2pl": "ardes", "3pl": "arem"}),
    "gerundio": ("stem", {"all": "ando"}),
    "participio_passado": ("stem", {"all": "ado"}),
}

# -car/-çar/-gar verbs harden their stem's final consonant before an ending
# that starts with "e", to keep the consonant's sound (c/g would otherwise
# soften before e, and ç is only ever written before a/o/u):
# ficar -> fiquei/fique, começar -> comecei/comece, pagar -> paguei/pague.
# Endings starting with "e" only ever appear attached to the bare stem (the
# "lemma"-based endings on futuro_indicativo/condicional attach after the
# full "-ar", so the stem's last letter there is never actually before an
# "e").
HARDENING = {"c": "qu", "ç": "c", "g": "gu"}



def _hardened_stem(stem: str) -> str | None:
    if not stem or stem[-1] not in HARDENING:
        return None
    return stem[:-1] + HARDENING[stem[-1]]


def transform(lemma: str, verb: Verb) -> Verb:
    verb = copy.deepcopy(verb)
    stem = lemma[:-2]
    hardened_stem = _hardened_stem(stem)

    for tense_name, (base, endings) in ENDING_RULES.items():
        verb[tense_name].update(
            {
                person: (
                    lemma if base == "lemma"
                    else hardened_stem if hardened_stem and ending.startswith("e")
                    else stem
                ) + ending
                for person, ending in endings.items()
            }
        )

    return verb


def notes(lemma: str, forms: Verb | None = None) -> dict[str, dict[str, str]]:
    stem = lemma[:-2]
    hardened_stem = _hardened_stem(stem)

    result: dict[str, dict[str, str]] = {}
    for tense_name, (base, endings) in ENDING_RULES.items():
        for person, ending in endings.items():
            if base == "lemma":
                generated, kwargs = lemma + ending, {"on_infinitive": True}
            elif hardened_stem and ending.startswith("e"):
                generated = hardened_stem + ending
                kwargs = {"spelling_change": (stem[-1], HARDENING[stem[-1]])}
            else:
                generated, kwargs = stem + ending, {}
            form = generated if forms is None else forms.get(tense_name, {}).get(person)
            note = conjugated_form_note(form, generated, ending, "-ar", **kwargs)
            if note:
                result.setdefault(tense_name, {})[person] = note

    return result
