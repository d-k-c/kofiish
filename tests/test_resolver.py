import re
import unittest
from pathlib import Path

from kofiish.deck import Deck, DeckLoader, DeckMetadata, DeckTenseCfg, Metadata, ModelMetadata
from kofiish.resolver import VerbExpander, VerbResolver, resolve_verb
from kofiish.transformation import TransformationLoader, authored_note, form_note
from kofiish.verb import Context, VerbDefinition, VerbDefinitionYamlLoader


class VerbExpanderTests(unittest.TestCase):
    def setUp(self):
        self.deck = Deck(
            metadata=Metadata(
                model=ModelMetadata(id=1, name="test model"),
                deck=DeckMetadata(id=2, name="test deck"),
                language="testlang",
            ),
            fields=(),
            pronouns={},
            tense_cfgs={
                "present": DeckTenseCfg(forms=("1sg", "3sg"), cue=None),
                "gerund": DeckTenseCfg(forms=("all",), cue=None),
            },
            verb_order=(),
        )

    def test_creates_every_deck_configured_tense_and_form(self):
        expanded = VerbExpander(self.deck).expand("cantar")

        self.assertEqual(set(expanded), {"present", "gerund"})
        self.assertEqual(set(expanded["present"]), {"1sg", "3sg"})
        self.assertEqual(set(expanded["gerund"]), {"all"})
        self.assertIsNone(expanded["present"]["1sg"])

    def test_loads_a_transformation_from_the_portuguese_deck(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        forms = VerbExpander(deck).expand("cantar")
        transform = TransformationLoader(
            Path("decks/pt/transformations")
        ).load("conjugator_ar")

        conjugated = transform("cantar", forms)

        self.assertEqual(conjugated["presente_indicativo"]["1sg"], "canto")
        self.assertEqual(conjugated["gerundio"]["all"], "cantando")


class VerbResolverTests(unittest.TestCase):
    def setUp(self):
        self.deck = Deck(
            metadata=Metadata(
                model=ModelMetadata(id=1, name="test model"),
                deck=DeckMetadata(id=2, name="test deck"),
                language="testlang",
            ),
            fields=(),
            pronouns={},
            tense_cfgs={
                "present": DeckTenseCfg(forms=("1sg", "3sg"), cue=None),
                "gerund": DeckTenseCfg(forms=("all",), cue=None),
            },
            verb_order=(),
        )

    def test_overlays_authored_forms_over_generated_ones_without_mutating_them(self):
        class FakeTransformationLoader:
            def load(self, name):
                def transform(lemma, verb):
                    verb = dict(verb)
                    verb["present"] = {**verb["present"], "1sg": "generated form"}
                    return verb
                return transform

        resolver = VerbResolver(VerbExpander(self.deck), FakeTransformationLoader())
        overrides = {"present": {"1sg": "tenho"}}

        resolved = resolver.resolve("ter", ("fake",), overrides)

        self.assertEqual(resolved["present"]["1sg"], "tenho")
        self.assertIsNone(resolved["present"]["3sg"])
        self.assertNotIn("gerund", overrides)

    def test_resolves_any_lemma_identically_main_verb_or_analog(self):
        resolver = VerbResolver(
            VerbExpander(DeckLoader().load(Path("decks/pt/deck.yaml"))),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        cantar = resolver.resolve("cantar", ("conjugator_ar",), {})
        falar = resolver.resolve("falar", ("conjugator_ar",), {"presente_indicativo": {"1sg": "override"}})

        self.assertEqual(cantar["presente_indicativo"]["1sg"], "canto")
        self.assertEqual(falar["presente_indicativo"]["1sg"], "override")
        self.assertEqual(falar["presente_indicativo"]["2sg"], "falas")


class ResolveVerbTests(unittest.TestCase):
    def test_composes_forms_contexts_and_analogs_without_mutating_source(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        source = VerbDefinition(
            lemma="cantar",
            translation="to sing",
            transformations=("conjugator_ar",),
            forms={},
            contexts={"presente_indicativo": {"default": Context(cue="Agora")}},
            analogs={"falar": {"presente_indicativo": {"1sg": "override"}}},
        )
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        resolved = resolve_verb(resolver, source)

        self.assertEqual(resolved.forms["presente_indicativo"]["1sg"], "canto")
        self.assertEqual(resolved.contexts["presente_indicativo"]["default"].cue, "Agora")
        self.assertEqual(resolved.analogs["falar"]["presente_indicativo"]["1sg"], "override")
        self.assertEqual(resolved.analogs["falar"]["presente_indicativo"]["2sg"], "falas")
        self.assertNotIn("gerund", source.forms)

    def test_authored_notes_are_appended_to_transformation_notes(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        source = VerbDefinition(
            lemma="ficar",
            translation="to stay",
            transformations=("conjugator_ar",),
            notes={
                "preterito_perfeito_indicativo": {"1sg": "authored addition"},
                "presente_indicativo": {"1sg": "authored only"},
            },
        )
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        resolved = resolve_verb(resolver, source)

        generated = resolver.resolve_notes("ficar", ("conjugator_ar",))

        # transformation note, untouched by yaml authoring
        self.assertEqual(
            resolved.notes["presente_conjuntivo"]["3pl"], generated["presente_conjuntivo"]["3pl"]
        )
        # yaml note is shown after the transformation's note for the same person
        self.assertEqual(
            resolved.notes["preterito_perfeito_indicativo"]["1sg"],
            generated["preterito_perfeito_indicativo"]["1sg"] + "<br>" + authored_note("authored addition"),
        )
        self.assertEqual(
            resolved.notes["presente_indicativo"]["1sg"],
            generated["presente_indicativo"]["1sg"] + "<br>" + authored_note("authored only"),
        )

    def test_a_pattern_is_shown_on_every_card_of_its_tense(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        source = VerbDefinition(
            lemma="ter",
            translation="to have",
            transformations=("ter_compound",),
            notes={"preterito_imperfeito_indicativo": {"1pl": "one-off"}},
            patterns={"preterito_imperfeito_indicativo": "stem `tinh-`"},
        )
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        resolved = resolve_verb(resolver, source)

        tense_notes = resolved.notes["preterito_imperfeito_indicativo"]
        self.assertEqual(tense_notes.keys(), {"1sg", "2sg", "3sg", "1pl", "2pl", "3pl"})
        self.assertEqual(tense_notes["1sg"], authored_note("stem `tinh-`"))
        # the tense's pattern comes after a per-cell note
        self.assertEqual(tense_notes["1pl"], authored_note("one-off") + "<br>" + authored_note("stem `tinh-`"))
        self.assertNotIn("presente_indicativo", resolved.notes)

    def test_an_overridden_form_drops_the_transformation_note(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        source = VerbDefinition(
            lemma="pagar",
            translation="to pay",
            transformations=("conjugator_ar",),
            forms={"participio_passado": {"all": "pago"}},
        )
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        resolved = resolve_verb(resolver, source)

        self.assertNotIn("all", resolved.notes.get("participio_passado", {}))
        self.assertIn("all", resolved.notes["gerundio"])

    def test_an_override_keeping_the_regular_ending_notes_only_the_ending(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        source = VerbDefinition(
            lemma="pedir",
            translation="to ask for",
            transformations=("conjugator_ir",),
            forms={"presente_indicativo": {"1sg": "peço"}},
            notes={"presente_indicativo": {"1sg": "stem `peç-`"}},
        )
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        resolved = resolve_verb(resolver, source)

        self.assertEqual(
            resolved.notes["presente_indicativo"]["1sg"],
            form_note("o", "-ir") + "<br>" + authored_note("stem `peç-`"),
        )

    def test_an_override_restating_the_generated_form_keeps_its_note(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        source = VerbDefinition(
            lemma="chover",
            translation="to rain",
            transformations=("conjugator_er",),
            forms={"presente_indicativo": {"1sg": None, "3sg": "chove"}},
        )
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        resolved = resolve_verb(resolver, source)

        self.assertIn("3sg", resolved.notes["presente_indicativo"])
        self.assertNotIn("1sg", resolved.notes["presente_indicativo"])

    def test_authored_note_identical_to_the_generated_one_is_not_repeated(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        source = VerbDefinition(
            lemma="ficar",
            translation="to stay",
            transformations=("conjugator_ar",),
            notes={"preterito_perfeito_indicativo": {"1sg": "`-ei` is the regular ending for verbs in -ar. The spelling change `c → qu` is considered regular (preserves pronunciation)."}},
        )
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )
        generated = resolver.resolve_notes("ficar", ("conjugator_ar",))

        resolved = resolve_verb(resolver, source)

        self.assertEqual(
            resolved.notes["preterito_perfeito_indicativo"]["1sg"],
            generated["preterito_perfeito_indicativo"]["1sg"],
        )


class AuthoredNotesDoNotDuplicateGeneratedOnesTests(unittest.TestCase):
    """Deck-wide guard: a hand-authored note sharing a cell with a
    transformation's note must add something, not restate it about the
    same forms."""

    def test_no_authored_note_highlights_a_form_its_generated_note_covers(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )
        highlighted = re.compile(r'class="(?:notes_sp_form|wrong_conj)">([^<]+)<')

        for path in sorted(Path("decks/pt/verbs").glob("*.yaml")):
            source = VerbDefinitionYamlLoader().load(path)
            forms = resolver.resolve(source.lemma, source.transformations, source.forms)
            generated = resolver.resolve_notes(source.lemma, source.transformations, forms)
            for tense_name, tense_notes in source.notes.items():
                for person, text in tense_notes.items():
                    generated_note = generated.get(tense_name, {}).get(person)
                    if generated_note is None:
                        continue
                    with self.subTest(verb=source.lemma, tense=tense_name, person=person):
                        shared = set(highlighted.findall(generated_note)) & set(
                            highlighted.findall(authored_note(text))
                        )
                        self.assertFalse(shared, f"restates the generated note about {shared}")



class NotesSharedByAWholeTenseArePatternsTests(unittest.TestCase):
    """Deck-wide guard: a note repeated on every card of a tense (typically
    "[[Irregular]]: The tense uses the stem `X-`.") belongs in the tense's
    `pattern:`, written once."""

    def test_no_tense_repeats_the_same_note_on_every_card(self):
        deck = DeckLoader().load(Path("decks/pt/deck.yaml"))
        resolver = VerbResolver(
            VerbExpander(deck),
            TransformationLoader(Path("decks/pt/transformations")),
        )

        for path in sorted(Path("decks/pt/verbs").glob("*.yaml")):
            source = VerbDefinitionYamlLoader().load(path)
            forms = resolver.resolve(source.lemma, source.transformations, source.forms)
            for tense_name, tense_notes in source.notes.items():
                persons = {person for person, form in forms.get(tense_name, {}).items() if form}
                if len(persons) < 2 or not persons <= tense_notes.keys():
                    continue
                with self.subTest(verb=source.lemma, tense=tense_name):
                    texts = {tense_notes[person] for person in persons}
                    self.assertGreater(len(texts), 1, "same note on every card: use `pattern:`")


if __name__ == "__main__":
    unittest.main()
