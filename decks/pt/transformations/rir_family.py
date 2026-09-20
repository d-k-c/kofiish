"""Conjugate 'rir'-family verbs: sorrir and others that end in "-rir" and inflect
exactly like "rir" with a different stem (sorrio, sorris, sorri, sorrimos,
sorrireis, ...).

The stem ending changes predictably (ri -> ride in 2pl, rir -> rides in
infinitive forms with a suffix), and accents in the imperfect and imperfect
subjunctive follow the expected pattern (ríamos, ríeis, ríssemos, rísseis).
"""

from __future__ import annotations

from kofiish.transformation import stem_family
from kofiish.verb import Verb

# "rir"'s own paradigm. Kept here rather than read from rir.yaml because a
# transformation is a pure function of (lemma, skeleton) with no knowledge of
# other verb files.
RIR_FORMS: Verb = {
    "presente_indicativo": {"1sg": "rio", "2sg": "ris", "3sg": "ri", "1pl": "rimos", "2pl": "rides", "3pl": "riem"},
    "preterito_perfeito_indicativo": {"1sg": "ri", "2sg": "riste", "3sg": "riu", "1pl": "rimos", "2pl": "ristes", "3pl": "riram"},
    "preterito_imperfeito_indicativo": {"1sg": "ria", "2sg": "rias", "3sg": "ria", "1pl": "ríamos", "2pl": "ríeis", "3pl": "riam"},
    "futuro_indicativo": {"1sg": "rirei", "2sg": "rirás", "3sg": "rirá", "1pl": "riremos", "2pl": "rireis", "3pl": "rirão"},
    "condicional": {"1sg": "riria", "2sg": "ririas", "3sg": "riria", "1pl": "riríamos", "2pl": "riríeis", "3pl": "ririam"},
    "presente_conjuntivo": {"1sg": "ria", "2sg": "rias", "3sg": "ria", "1pl": "riamos", "2pl": "riais", "3pl": "riam"},
    "preterito_imperfeito_conjuntivo": {"1sg": "risse", "2sg": "risses", "3sg": "risse", "1pl": "ríssemos", "2pl": "rísseis", "3pl": "rissem"},
    "futuro_conjuntivo": {"1sg": "rir", "2sg": "rires", "3sg": "rir", "1pl": "rirmos", "2pl": "rirdes", "3pl": "rirem"},
    "imperativo_afirmativo": {"2sg": "ri", "3sg": "ria", "1pl": "riamos", "2pl": "ride", "3pl": "riam"},
    "imperativo_negativo": {"2sg": "rias", "3sg": "ria", "1pl": "riamos", "2pl": "riais", "3pl": "riam"},
    "infinitivo_pessoal": {"1sg": "rir", "2sg": "rires", "3sg": "rir", "1pl": "rirmos", "2pl": "rirdes", "3pl": "rirem"},
    "gerundio": {"all": "rindo"},
    "participio_passado": {"all": "rido"},
}


transform = stem_family("rir", "", RIR_FORMS)
