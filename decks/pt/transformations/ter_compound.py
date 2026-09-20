"""Conjugate 'ter'-family compound verbs: conter, deter, entreter, manter,
obter, reter, suster, and others that end in "-ter" and inflect exactly like
"ter" with a prefix glued on (contenho, detenho, retenho, ...).

A prefix isn't always a plain concatenation onto "ter"'s own written form,
because adding a prefix can turn one of "ter"'s monosyllabic forms into a
multi-syllable word, and Portuguese spelling then requires a written accent
that "tens"/"tem" alone don't need (tens -> conténs, tem -> contém).
"""

from __future__ import annotations

from kofiish.transformation import stem_family
from kofiish.verb import Verb

# "ter"'s own paradigm. Kept here rather than read from ter.yaml because a
# transformation is a pure function of (lemma, skeleton) with no knowledge of
# other verb files.
TER_FORMS: Verb = {
    "presente_indicativo": {"1sg": "tenho", "2sg": "tens", "3sg": "tem", "1pl": "temos", "2pl": "tendes", "3pl": "têm"},
    "preterito_perfeito_indicativo": {"1sg": "tive", "2sg": "tiveste", "3sg": "teve", "1pl": "tivemos", "2pl": "tivestes", "3pl": "tiveram"},
    "preterito_imperfeito_indicativo": {"1sg": "tinha", "2sg": "tinhas", "3sg": "tinha", "1pl": "tínhamos", "2pl": "tínheis", "3pl": "tinham"},
    "futuro_indicativo": {"1sg": "terei", "2sg": "terás", "3sg": "terá", "1pl": "teremos", "2pl": "tereis", "3pl": "terão"},
    "condicional": {"1sg": "teria", "2sg": "terias", "3sg": "teria", "1pl": "teríamos", "2pl": "teríeis", "3pl": "teriam"},
    "presente_conjuntivo": {"1sg": "tenha", "2sg": "tenhas", "3sg": "tenha", "1pl": "tenhamos", "2pl": "tenhais", "3pl": "tenham"},
    "preterito_imperfeito_conjuntivo": {"1sg": "tivesse", "2sg": "tivesses", "3sg": "tivesse", "1pl": "tivéssemos", "2pl": "tivésseis", "3pl": "tivessem"},
    "futuro_conjuntivo": {"1sg": "tiver", "2sg": "tiveres", "3sg": "tiver", "1pl": "tivermos", "2pl": "tiverdes", "3pl": "tiverem"},
    "imperativo_afirmativo": {"2sg": "tem", "3sg": "tenha", "1pl": "tenhamos", "2pl": "tende", "3pl": "tenham"},
    "imperativo_negativo": {"2sg": "tenhas", "3sg": "tenha", "1pl": "tenhamos", "2pl": "tenhais", "3pl": "tenham"},
    "infinitivo_pessoal": {"1sg": "ter", "2sg": "teres", "3sg": "ter", "1pl": "termos", "2pl": "terdes", "3pl": "terem"},
    "gerundio": {"all": "tendo"},
    "participio_passado": {"all": "tido"},
}

# Forms where prefixing turns a monosyllabic "ter" form into a multi-syllable
# oxytone, which needs an accent the base form doesn't carry.
ACCENTED_OVERRIDES = {
    ("presente_indicativo", "2sg"): "téns",
    ("presente_indicativo", "3sg"): "tém",
    ("imperativo_afirmativo", "2sg"): "tém",
}


transform = stem_family("ter", "", TER_FORMS, ACCENTED_OVERRIDES)
