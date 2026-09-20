"""Conjugate 'construir'-family verbs: destruir, reconstruir, and others that
end in "-struir" and inflect exactly like "construir" with a different stem
(destruo, destruis, destrui, destruem, destruímos, ...).

The present keeps the u (construis, construi, construem, imperative construi);
the u -> ó/o variants (constróis, constrói, constroem) also exist but are only
mentioned in construir.yaml's notes. The hiatus accents (construímos,
construíste, construído, ...) sit on the ending, so they carry over unchanged
to every stem.
"""

from __future__ import annotations

from kofiish.transformation import stem_family
from kofiish.verb import Verb

# "construir"'s own paradigm. Kept here rather than read from construir.yaml
# because a transformation is a pure function of (lemma, skeleton) with no
# knowledge of other verb files.
CONSTRUIR_FORMS: Verb = {
    "presente_indicativo": {"1sg": "construo", "2sg": "construis", "3sg": "construi", "1pl": "construímos", "2pl": "construís", "3pl": "construem"},
    "preterito_perfeito_indicativo": {"1sg": "construí", "2sg": "construíste", "3sg": "construiu", "1pl": "construímos", "2pl": "construístes", "3pl": "construíram"},
    "preterito_imperfeito_indicativo": {"1sg": "construía", "2sg": "construías", "3sg": "construía", "1pl": "construíamos", "2pl": "construíeis", "3pl": "construíam"},
    "futuro_indicativo": {"1sg": "construirei", "2sg": "construirás", "3sg": "construirá", "1pl": "construiremos", "2pl": "construireis", "3pl": "construirão"},
    "condicional": {"1sg": "construiria", "2sg": "construirias", "3sg": "construiria", "1pl": "construiríamos", "2pl": "construiríeis", "3pl": "construiriam"},
    "presente_conjuntivo": {"1sg": "construa", "2sg": "construas", "3sg": "construa", "1pl": "construamos", "2pl": "construais", "3pl": "construam"},
    "preterito_imperfeito_conjuntivo": {"1sg": "construísse", "2sg": "construísses", "3sg": "construísse", "1pl": "construíssemos", "2pl": "construísseis", "3pl": "construíssem"},
    "futuro_conjuntivo": {"1sg": "construir", "2sg": "construíres", "3sg": "construir", "1pl": "construirmos", "2pl": "construirdes", "3pl": "construírem"},
    "imperativo_afirmativo": {"2sg": "construi", "3sg": "construa", "1pl": "construamos", "2pl": "construí", "3pl": "construam"},
    "imperativo_negativo": {"2sg": "construas", "3sg": "construa", "1pl": "construamos", "2pl": "construais", "3pl": "construam"},
    "infinitivo_pessoal": {"1sg": "construir", "2sg": "construíres", "3sg": "construir", "1pl": "construirmos", "2pl": "construirdes", "3pl": "construírem"},
    "gerundio": {"all": "construindo"},
    "participio_passado": {"all": "construído"},
}


transform = stem_family("construir", "con", CONSTRUIR_FORMS)
