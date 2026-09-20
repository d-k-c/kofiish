"""Conjugate 'sair'-family verbs: cair, atrair, trair, distrair, and others
that end in "-air" and inflect exactly like "sair" with a different stem
(caio, caímos, atraíste, traído, ...).

The hiatus accents (saímos, saíste, saído, ...) sit on the ending, so they
carry over unchanged to every stem.
"""

from __future__ import annotations

from kofiish.transformation import stem_family
from kofiish.verb import Verb

# "sair"'s own paradigm. Kept here rather than read from sair.yaml because a
# transformation is a pure function of (lemma, skeleton) with no knowledge of
# other verb files.
SAIR_FORMS: Verb = {
    "presente_indicativo": {"1sg": "saio", "2sg": "sais", "3sg": "sai", "1pl": "saímos", "2pl": "saís", "3pl": "saem"},
    "preterito_perfeito_indicativo": {"1sg": "saí", "2sg": "saíste", "3sg": "saiu", "1pl": "saímos", "2pl": "saístes", "3pl": "saíram"},
    "preterito_imperfeito_indicativo": {"1sg": "saía", "2sg": "saías", "3sg": "saía", "1pl": "saíamos", "2pl": "saíeis", "3pl": "saíam"},
    "futuro_indicativo": {"1sg": "sairei", "2sg": "sairás", "3sg": "sairá", "1pl": "sairemos", "2pl": "saireis", "3pl": "sairão"},
    "condicional": {"1sg": "sairia", "2sg": "sairias", "3sg": "sairia", "1pl": "sairíamos", "2pl": "sairíeis", "3pl": "sairiam"},
    "presente_conjuntivo": {"1sg": "saia", "2sg": "saias", "3sg": "saia", "1pl": "saiamos", "2pl": "saiais", "3pl": "saiam"},
    "preterito_imperfeito_conjuntivo": {"1sg": "saísse", "2sg": "saísses", "3sg": "saísse", "1pl": "saíssemos", "2pl": "saísseis", "3pl": "saíssem"},
    "futuro_conjuntivo": {"1sg": "sair", "2sg": "saíres", "3sg": "sair", "1pl": "sairmos", "2pl": "sairdes", "3pl": "saírem"},
    "imperativo_afirmativo": {"2sg": "sai", "3sg": "saia", "1pl": "saiamos", "2pl": "saí", "3pl": "saiam"},
    "imperativo_negativo": {"2sg": "saias", "3sg": "saia", "1pl": "saiamos", "2pl": "saiais", "3pl": "saiam"},
    "infinitivo_pessoal": {"1sg": "sair", "2sg": "saíres", "3sg": "sair", "1pl": "sairmos", "2pl": "sairdes", "3pl": "saírem"},
    "gerundio": {"all": "saindo"},
    "participio_passado": {"all": "saído"},
}


transform = stem_family("sair", "s", SAIR_FORMS)
