"""Conjugate 'ler'-family verbs: reler, crer, descrer, and others that end in
"-er" and inflect exactly like "ler" with a different stem (releio, creio,
crês, credes, creem, crido, ...).

Only for verbs sharing ler's own irregular diphthong/accent pattern; a
regular "-er" verb belongs to conjugator_er.
"""

from __future__ import annotations

from kofiish.transformation import stem_family
from kofiish.verb import Verb

# "ler"'s own paradigm. Kept here rather than read from ler.yaml because a
# transformation is a pure function of (lemma, skeleton) with no knowledge of
# other verb files.
LER_FORMS: Verb = {
    "presente_indicativo": {"1sg": "leio", "2sg": "lês", "3sg": "lê", "1pl": "lemos", "2pl": "ledes", "3pl": "leem"},
    "preterito_perfeito_indicativo": {"1sg": "li", "2sg": "leste", "3sg": "leu", "1pl": "lemos", "2pl": "lestes", "3pl": "leram"},
    "preterito_imperfeito_indicativo": {"1sg": "lia", "2sg": "lias", "3sg": "lia", "1pl": "líamos", "2pl": "líeis", "3pl": "liam"},
    "futuro_indicativo": {"1sg": "lerei", "2sg": "lerás", "3sg": "lerá", "1pl": "leremos", "2pl": "lereis", "3pl": "lerão"},
    "condicional": {"1sg": "leria", "2sg": "lerias", "3sg": "leria", "1pl": "leríamos", "2pl": "leríeis", "3pl": "leriam"},
    "presente_conjuntivo": {"1sg": "leia", "2sg": "leias", "3sg": "leia", "1pl": "leiamos", "2pl": "leiais", "3pl": "leiam"},
    "preterito_imperfeito_conjuntivo": {"1sg": "lesse", "2sg": "lesses", "3sg": "lesse", "1pl": "lêssemos", "2pl": "lêsseis", "3pl": "lessem"},
    "futuro_conjuntivo": {"1sg": "ler", "2sg": "leres", "3sg": "ler", "1pl": "lermos", "2pl": "lerdes", "3pl": "lerem"},
    "imperativo_afirmativo": {"2sg": "lê", "3sg": "leia", "1pl": "leiamos", "2pl": "lede", "3pl": "leiam"},
    "imperativo_negativo": {"2sg": "leias", "3sg": "leia", "1pl": "leiamos", "2pl": "leiais", "3pl": "leiam"},
    "infinitivo_pessoal": {"1sg": "ler", "2sg": "leres", "3sg": "ler", "1pl": "lermos", "2pl": "lerdes", "3pl": "lerem"},
    "gerundio": {"all": "lendo"},
    "participio_passado": {"all": "lido"},
}


transform = stem_family("ler", "l", LER_FORMS)
