import unittest
from pathlib import Path

from kofiish.deck import DeckLoader
from kofiish.resolver import VerbExpander
from kofiish.transformation import TransformationLoader, authored_note, form_note


class AuthoredNoteTests(unittest.TestCase):
    def test_markup_becomes_the_same_spans_the_generated_notes_use(self):
        self.assertEqual(
            authored_note("`Faço` is irregular — not the expected *fazo*."),
            '<span class="SECTION_regularity">'
            '<span class="notes_sp_form">Faço</span> is irregular — not the expected '
            '<span class="wrong_conj">fazo</span>.</span>',
        )

    def test_spelling_change_and_feature_markers(self):
        self.assertEqual(
            authored_note("[[Irregular]]: ~d → ç~ in `peço`"),
            '<span class="SECTION_regularity">'
            '<span class="note_feature">Irregular</span>: '
            '<span class="note_spell">d → ç</span> in '
            '<span class="notes_sp_form">peço</span></span>',
        )

    def test_newlines_become_line_breaks_without_a_trailing_one(self):
        # a YAML "|" block ends with a newline, which shouldn't add an empty line
        self.assertEqual(
            authored_note("first line\nsecond line\n"),
            '<span class="SECTION_regularity">first line<br>second line</span>',
        )

    def test_plain_text_is_escaped_and_wrapped(self):
        self.assertEqual(
            authored_note('a < b & "c"'),
            '<span class="SECTION_regularity">a &lt; b &amp; "c"</span>',
        )


class TerCompoundTests(unittest.TestCase):
    def setUp(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        self.expander = VerbExpander(deck)
        self.transform = TransformationLoader(Path("decks/pt/transformations")).load("ter_compound")

    def test_plain_prefixing_for_unaccented_forms(self):
        conjugated = self.transform("conter", self.expander.expand("conter"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "contenho")
        self.assertEqual(conjugated["gerundio"]["all"], "contendo")

    def test_inserts_accent_when_prefixing_makes_the_form_multisyllabic(self):
        conjugated = self.transform("conter", self.expander.expand("conter"))

        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "conténs")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "contém")

    def test_keeps_proparoxytone_accent_prefix_invariant(self):
        conjugated = self.transform("suster", self.expander.expand("suster"))

        self.assertEqual(conjugated["preterito_imperfeito_indicativo"]["1pl"], "sustínhamos")

    def test_plain_prefixing_for_imperativo_negativo(self):
        conjugated = self.transform("reter", self.expander.expand("reter"))

        self.assertEqual(conjugated["imperativo_negativo"]["2sg"], "retenhas")

    def test_applied_to_ter_itself_leaves_the_base_forms_unaccented(self):
        conjugated = self.transform("ter", self.expander.expand("ter"))

        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "tens")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "tem")

    def test_rejects_a_lemma_that_does_not_end_in_ter(self):
        with self.assertRaises(ValueError):
            self.transform("cantar", self.expander.expand("cantar"))


class VirCompoundTests(unittest.TestCase):
    def setUp(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        self.expander = VerbExpander(deck)
        self.transform = TransformationLoader(Path("decks/pt/transformations")).load("vir_compound")

    def test_plain_prefixing_for_unaccented_forms(self):
        conjugated = self.transform("intervir", self.expander.expand("intervir"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "intervenho")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1sg"], "intervim")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["3sg"], "interveio")
        self.assertEqual(conjugated["participio_passado"]["all"], "intervindo")

    def test_inserts_accent_when_prefixing_makes_the_form_multisyllabic(self):
        conjugated = self.transform("intervir", self.expander.expand("intervir"))

        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "intervéns")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "intervém")
        self.assertEqual(conjugated["imperativo_afirmativo"]["2sg"], "intervém")

    def test_keeps_the_3pl_circumflex(self):
        conjugated = self.transform("provir", self.expander.expand("provir"))

        self.assertEqual(conjugated["presente_indicativo"]["3pl"], "provêm")

    def test_applied_to_vir_itself_leaves_the_base_forms_unaccented(self):
        conjugated = self.transform("vir", self.expander.expand("vir"))

        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "vens")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "vem")

    def test_rejects_a_lemma_that_does_not_end_in_vir(self):
        with self.assertRaises(ValueError):
            self.transform("partir", self.expander.expand("partir"))


class StemFamilyTests(unittest.TestCase):
    def setUp(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        self.expander = VerbExpander(deck)
        self.loader = TransformationLoader(Path("decks/pt/transformations"))

    def conjugate(self, family, lemma):
        return self.loader.load(family)(lemma, self.expander.expand(lemma))

    def test_ver_family_prefixes_and_keeps_accents(self):
        conjugated = self.conjugate("ver_family", "antever")

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "antevejo")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "antevê")
        self.assertEqual(conjugated["futuro_conjuntivo"]["1sg"], "antevir")
        self.assertEqual(conjugated["participio_passado"]["all"], "antevisto")

    def test_ler_family_swaps_the_stem_for_crer(self):
        conjugated = self.conjugate("ler_family", "descrer")

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "descreio")
        self.assertEqual(conjugated["presente_indicativo"]["3pl"], "descreem")
        self.assertEqual(conjugated["preterito_imperfeito_conjuntivo"]["1pl"], "descrêssemos")

    def test_sair_family_keeps_the_hiatus_accents(self):
        conjugated = self.conjugate("sair_family", "distrair")

        self.assertEqual(conjugated["presente_indicativo"]["1pl"], "distraímos")
        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "distrais")
        self.assertEqual(conjugated["futuro_conjuntivo"]["3pl"], "distraírem")
        self.assertEqual(conjugated["participio_passado"]["all"], "distraído")

    def test_construir_family_keeps_the_u_and_hiatus_accents(self):
        conjugated = self.conjugate("construir_family", "destruir")

        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "destruis")
        self.assertEqual(conjugated["presente_indicativo"]["3pl"], "destruem")
        self.assertEqual(conjugated["presente_indicativo"]["1pl"], "destruímos")
        self.assertEqual(conjugated["futuro_conjuntivo"]["3pl"], "destruírem")
        self.assertEqual(conjugated["participio_passado"]["all"], "destruído")

    def test_construir_family_rejects_other_uir_verbs(self):
        with self.assertRaises(ValueError):
            self.conjugate("construir_family", "atribuir")

    def test_rir_family_keeps_the_stem_structure_and_accents(self):
        conjugated = self.conjugate("rir_family", "sorrir")

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "sorrio")
        self.assertEqual(conjugated["presente_indicativo"]["2pl"], "sorrides")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "sorri")
        self.assertEqual(conjugated["presente_indicativo"]["3pl"], "sorriem")
        self.assertEqual(conjugated["preterito_imperfeito_indicativo"]["1pl"], "sorríamos")
        self.assertEqual(conjugated["preterito_imperfeito_indicativo"]["2pl"], "sorríeis")
        self.assertEqual(conjugated["preterito_imperfeito_conjuntivo"]["1pl"], "sorríssemos")
        self.assertEqual(conjugated["participio_passado"]["all"], "sorrido")

    def test_rir_family_rejects_verbs_outside_the_family(self):
        with self.assertRaises(ValueError):
            self.conjugate("rir_family", "partir")

    def test_rejects_a_lemma_outside_the_family(self):
        with self.assertRaises(ValueError):
            self.conjugate("sair_family", "partir")


class ConjugatorArTests(unittest.TestCase):
    def setUp(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        self.expander = VerbExpander(deck)
        loader = TransformationLoader(Path("decks/pt/transformations"))
        self.transform = loader.load("conjugator_ar")
        self.notes = loader.load_notes("conjugator_ar")

    def test_regular_verb_is_unaffected(self):
        conjugated = self.transform("cantar", self.expander.expand("cantar"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "canto")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1sg"], "cantei")
        self.assertEqual(conjugated["presente_conjuntivo"]["1sg"], "cante")

    def test_every_form_gets_a_regular_ending_note(self):
        notes = self.notes("cantar")

        self.assertEqual(notes["presente_indicativo"]["1sg"], form_note("o", "-ar"))
        self.assertEqual(
            notes["futuro_indicativo"]["1sg"], form_note("ei", "-ar", on_infinitive=True)
        )
        self.assertEqual(notes["gerundio"]["all"], form_note("ando", "-ar"))

    def test_spelling_change_line_renders_with_the_deck_classes(self):
        self.assertEqual(
            form_note("ei", "-ar", spelling_change=("g", "gu")),
            '<span class="SECTION_regularity">'
            '<span class="notes_sp_form">-ei</span> is the regular ending for verbs in '
            '<span class="note_spell">-ar</span>.'
            '<br>The <span class="note_feature">spelling change</span> '
            '<span class="note_spell">g → gu</span> is considered regular '
            "(preserves pronunciation).</span>",
        )

    def test_preterito_perfeito_1pl_is_accented_unlike_presente(self):
        conjugated = self.transform("cantar", self.expander.expand("cantar"))

        self.assertEqual(conjugated["presente_indicativo"]["1pl"], "cantamos")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1pl"], "cantámos")

    def test_car_verb_hardens_c_to_qu_before_e(self):
        conjugated = self.transform("ficar", self.expander.expand("ficar"))

        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1sg"], "fiquei")
        self.assertEqual(conjugated["presente_conjuntivo"]["1sg"], "fique")
        self.assertEqual(conjugated["imperativo_negativo"]["2sg"], "fiques")
        # unaffected: presente_indicativo endings don't start with "e"
        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "fico")

    def test_car_verb_notes_explain_the_hardening_only_where_it_applies(self):
        notes = self.notes("chegar")

        self.assertEqual(
            notes["preterito_perfeito_indicativo"]["1sg"], form_note("ei", "-ar", spelling_change=("g", "gu"))
        )
        self.assertEqual(notes["presente_conjuntivo"]["3pl"], form_note("em", "-ar", spelling_change=("g", "gu")))
        self.assertEqual(notes["presente_indicativo"]["1sg"], form_note("o", "-ar"))

    def test_car_verb_futuro_and_condicional_use_the_full_lemma_unhardened(self):
        conjugated = self.transform("ficar", self.expander.expand("ficar"))

        self.assertEqual(conjugated["futuro_indicativo"]["1sg"], "ficarei")
        self.assertEqual(conjugated["condicional"]["1sg"], "ficaria")

    def test_ar_verb_softens_c_to_c_before_e(self):
        conjugated = self.transform("começar", self.expander.expand("começar"))

        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1sg"], "comecei")
        self.assertEqual(conjugated["presente_conjuntivo"]["1sg"], "comece")
        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "começo")

    def test_gar_verb_hardens_g_to_gu_before_e(self):
        conjugated = self.transform("pagar", self.expander.expand("pagar"))

        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1sg"], "paguei")
        self.assertEqual(conjugated["presente_conjuntivo"]["1sg"], "pague")
        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "pago")


class ConjugatorErTests(unittest.TestCase):
    def setUp(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        self.expander = VerbExpander(deck)
        loader = TransformationLoader(Path("decks/pt/transformations"))
        self.transform = loader.load("conjugator_er")
        self.notes = loader.load_notes("conjugator_er")

    def test_regular_verb_is_unaffected(self):
        conjugated = self.transform("vender", self.expander.expand("vender"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "vendo")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["3sg"], "vendeu")
        self.assertEqual(conjugated["preterito_imperfeito_conjuntivo"]["1pl"], "vendêssemos")
        self.assertEqual(conjugated["imperativo_afirmativo"]["2pl"], "vendei")
        self.assertEqual(conjugated["participio_passado"]["all"], "vendido")

    def test_every_form_gets_a_regular_ending_note(self):
        notes = self.notes("vender")

        self.assertEqual(notes["preterito_perfeito_indicativo"]["3sg"], form_note("eu", "-er"))
        self.assertEqual(notes["presente_conjuntivo"]["1sg"], form_note("a", "-er"))

    def test_cer_verb_softens_c_to_c_before_a_and_o(self):
        conjugated = self.transform("parecer", self.expander.expand("parecer"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "pareço")
        self.assertEqual(conjugated["presente_conjuntivo"]["1pl"], "pareçamos")
        self.assertEqual(conjugated["imperativo_afirmativo"]["3sg"], "pareça")
        # unaffected: endings starting with "e"/"i"
        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "pareces")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1sg"], "pareci")
        self.assertEqual(conjugated["imperativo_afirmativo"]["2sg"], "parece")

    def test_ger_verb_softens_g_to_j_before_a_and_o(self):
        conjugated = self.transform("proteger", self.expander.expand("proteger"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "protejo")
        self.assertEqual(conjugated["imperativo_negativo"]["2sg"], "protejas")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "protege")

    def test_guer_verb_drops_the_u_before_a_and_o(self):
        conjugated = self.transform("erguer", self.expander.expand("erguer"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "ergo")
        self.assertEqual(conjugated["presente_conjuntivo"]["3pl"], "ergam")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "ergue")

    def test_cer_verb_notes_explain_the_softening_only_where_it_applies(self):
        notes = self.notes("parecer")
        softened = form_note("o", "-er", spelling_change=("c", "ç"))

        self.assertEqual(notes["presente_indicativo"]["1sg"], softened)
        self.assertEqual(notes["presente_indicativo"]["2sg"], form_note("es", "-er"))
        self.assertEqual(
            notes["imperativo_afirmativo"]["3sg"], form_note("a", "-er", spelling_change=("c", "ç"))
        )
        self.assertEqual(notes["futuro_indicativo"]["1sg"], form_note("ei", "-er", on_infinitive=True))
        self.assertEqual(notes["gerundio"]["all"], form_note("endo", "-er"))

    def test_guer_verb_notes_show_the_dropped_u(self):
        notes = self.notes("erguer")

        self.assertEqual(
            notes["presente_indicativo"]["1sg"], form_note("o", "-er", spelling_change=("gu", "g"))
        )


class ConjugatorIrTests(unittest.TestCase):
    def setUp(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        self.expander = VerbExpander(deck)
        loader = TransformationLoader(Path("decks/pt/transformations"))
        self.transform = loader.load("conjugator_ir")
        self.notes = loader.load_notes("conjugator_ir")

    def test_regular_verb_is_unaffected(self):
        conjugated = self.transform("partir", self.expander.expand("partir"))

        self.assertEqual(conjugated["presente_indicativo"]["2pl"], "partis")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["3sg"], "partiu")
        self.assertEqual(conjugated["preterito_imperfeito_conjuntivo"]["2pl"], "partísseis")
        self.assertEqual(conjugated["imperativo_afirmativo"]["2pl"], "parti")
        self.assertEqual(conjugated["gerundio"]["all"], "partindo")

    def test_every_form_gets_a_regular_ending_note(self):
        notes = self.notes("partir")

        self.assertEqual(notes["presente_indicativo"]["2pl"], form_note("is", "-ir"))
        self.assertEqual(notes["condicional"]["1pl"], form_note("íamos", "-ir", on_infinitive=True))
        self.assertEqual(notes["participio_passado"]["all"], form_note("ido", "-ir"))

    def test_gir_verb_softens_g_to_j_before_a_and_o(self):
        conjugated = self.transform("exigir", self.expander.expand("exigir"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "exijo")
        self.assertEqual(conjugated["presente_conjuntivo"]["2sg"], "exijas")
        self.assertEqual(conjugated["presente_indicativo"]["2sg"], "exiges")
        self.assertEqual(conjugated["futuro_indicativo"]["1sg"], "exigirei")

    def test_guir_verb_drops_the_u_before_a_and_o(self):
        conjugated = self.transform("distinguir", self.expander.expand("distinguir"))

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "distingo")
        self.assertEqual(conjugated["imperativo_negativo"]["3pl"], "distingam")
        self.assertEqual(conjugated["presente_indicativo"]["3sg"], "distingue")
        self.assertEqual(conjugated["preterito_perfeito_indicativo"]["1sg"], "distingui")

    def test_gir_verb_notes_explain_the_softening_only_where_it_applies(self):
        notes = self.notes("exigir")
        softening = ("g", "j")

        self.assertEqual(notes["presente_indicativo"]["1sg"], form_note("o", "-ir", spelling_change=softening))
        self.assertEqual(
            notes["presente_conjuntivo"]["1pl"], form_note("amos", "-ir", spelling_change=softening)
        )
        self.assertEqual(notes["preterito_perfeito_indicativo"]["1sg"], form_note("i", "-ir"))

    def test_guir_verb_notes_show_the_dropped_u(self):
        notes = self.notes("distinguir")

        self.assertEqual(
            notes["presente_indicativo"]["1sg"], form_note("o", "-ir", spelling_change=("gu", "g"))
        )


if __name__ == "__main__":
    unittest.main()
