"""Conjugate 'ver'-family verbs: prever, rever, antever, and others that end
in "-ver" and inflect exactly like "ver" with a prefix glued on (prevejo,
prevê, previsto, ...).

"ver"'s accented monosyllables (vês, vê) keep their accent when prefixed
(prevês, prevê), so unlike ter_compound no form needs adjusting. "prover"
is NOT in this family (provi, provido): don't use it here.
"""

from __future__ import annotations

from kofiish.transformation import stem_family
from kofiish.verb import Verb

# "ver"'s own paradigm. Kept here rather than read from ver.yaml because a
# transformation is a pure function of (lemma, skeleton) with no knowledge of
# other verb files.
VER_FORMS: Verb = {
    "presente_indicativo": {"1sg": "vejo", "2sg": "vês", "3sg": "vê", "1pl": "vemos", "2pl": "vedes", "3pl": "veem"},
    "preterito_perfeito_indicativo": {"1sg": "vi", "2sg": "viste", "3sg": "viu", "1pl": "vimos", "2pl": "vistes", "3pl": "viram"},
    "preterito_imperfeito_indicativo": {"1sg": "via", "2sg": "vias", "3sg": "via", "1pl": "víamos", "2pl": "víeis", "3pl": "viam"},
    "futuro_indicativo": {"1sg": "verei", "2sg": "verás", "3sg": "verá", "1pl": "veremos", "2pl": "vereis", "3pl": "verão"},
    "condicional": {"1sg": "veria", "2sg": "verias", "3sg": "veria", "1pl": "veríamos", "2pl": "veríeis", "3pl": "veriam"},
    "presente_conjuntivo": {"1sg": "veja", "2sg": "vejas", "3sg": "veja", "1pl": "vejamos", "2pl": "vejais", "3pl": "vejam"},
    "preterito_imperfeito_conjuntivo": {"1sg": "visse", "2sg": "visses", "3sg": "visse", "1pl": "víssemos", "2pl": "vísseis", "3pl": "vissem"},
    "futuro_conjuntivo": {"1sg": "vir", "2sg": "vires", "3sg": "vir", "1pl": "virmos", "2pl": "virdes", "3pl": "virem"},
    "imperativo_afirmativo": {"2sg": "vê", "3sg": "veja", "1pl": "vejamos", "2pl": "vede", "3pl": "vejam"},
    "imperativo_negativo": {"2sg": "vejas", "3sg": "veja", "1pl": "vejamos", "2pl": "vejais", "3pl": "vejam"},
    "infinitivo_pessoal": {"1sg": "ver", "2sg": "veres", "3sg": "ver", "1pl": "vermos", "2pl": "verdes", "3pl": "verem"},
    "gerundio": {"all": "vendo"},
    "participio_passado": {"all": "visto"},
}


transform = stem_family("ver", "v", VER_FORMS)
