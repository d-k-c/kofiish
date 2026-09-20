"""Conjugate 'vir'-family compound verbs: intervir, provir, convir, sobrevir,
advir, and others that end in "-vir" and inflect exactly like "vir" with a
prefix glued on (intervenho, provenho, convenho, ...).

Same accent rule as ter_compound: prefixing turns "vir"'s monosyllabic
"vens"/"vem" into multi-syllable oxytones that need a written accent
(vens -> intervéns, vem -> intervém). "vêm" already carries its circumflex
and "vim" never takes an accent, so both are plain concatenations.
"""

from __future__ import annotations

from kofiish.transformation import stem_family
from kofiish.verb import Verb

# "vir"'s own paradigm. Kept here rather than read from vir.yaml because a
# transformation is a pure function of (lemma, skeleton) with no knowledge of
# other verb files.
VIR_FORMS: Verb = {
    "presente_indicativo": {"1sg": "venho", "2sg": "vens", "3sg": "vem", "1pl": "vimos", "2pl": "vindes", "3pl": "vêm"},
    "preterito_perfeito_indicativo": {"1sg": "vim", "2sg": "vieste", "3sg": "veio", "1pl": "viemos", "2pl": "viestes", "3pl": "vieram"},
    "preterito_imperfeito_indicativo": {"1sg": "vinha", "2sg": "vinhas", "3sg": "vinha", "1pl": "vínhamos", "2pl": "vínheis", "3pl": "vinham"},
    "futuro_indicativo": {"1sg": "virei", "2sg": "virás", "3sg": "virá", "1pl": "viremos", "2pl": "vireis", "3pl": "virão"},
    "condicional": {"1sg": "viria", "2sg": "virias", "3sg": "viria", "1pl": "viríamos", "2pl": "viríeis", "3pl": "viriam"},
    "presente_conjuntivo": {"1sg": "venha", "2sg": "venhas", "3sg": "venha", "1pl": "venhamos", "2pl": "venhais", "3pl": "venham"},
    "preterito_imperfeito_conjuntivo": {"1sg": "viesse", "2sg": "viesses", "3sg": "viesse", "1pl": "viéssemos", "2pl": "viésseis", "3pl": "viessem"},
    "futuro_conjuntivo": {"1sg": "vier", "2sg": "vieres", "3sg": "vier", "1pl": "viermos", "2pl": "vierdes", "3pl": "vierem"},
    "imperativo_afirmativo": {"2sg": "vem", "3sg": "venha", "1pl": "venhamos", "2pl": "vinde", "3pl": "venham"},
    "imperativo_negativo": {"2sg": "venhas", "3sg": "venha", "1pl": "venhamos", "2pl": "venhais", "3pl": "venham"},
    "infinitivo_pessoal": {"1sg": "vir", "2sg": "vires", "3sg": "vir", "1pl": "virmos", "2pl": "virdes", "3pl": "virem"},
    "gerundio": {"all": "vindo"},
    "participio_passado": {"all": "vindo"},
}


# Forms where prefixing turns a monosyllabic "vir" form into a multi-syllable
# oxytone, which needs an accent the base form doesn't carry.
ACCENTED_OVERRIDES = {
    ("presente_indicativo", "2sg"): "véns",
    ("presente_indicativo", "3sg"): "vém",
    ("imperativo_afirmativo", "2sg"): "vém",
}


transform = stem_family("vir", "", VIR_FORMS, ACCENTED_OVERRIDES)
