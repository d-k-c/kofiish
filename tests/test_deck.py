import contextlib
import io
import unittest
from pathlib import Path

from kofiish.deck import DeckLoader


class LoadVerbsTests(unittest.TestCase):
    def setUp(self):
        self.deck = DeckLoader().load(Path("decks/pt/deck.yaml"))

    def test_returns_verbs_in_deck_yamls_authored_order_minus_unauthored_ones(self):
        verbs = self.deck.load_verbs(Path("decks/pt/verbs"))

        authored = [lemma for lemma in self.deck.verb_order if lemma in verbs]
        self.assertEqual(list(verbs), authored)

    def test_skips_a_verb_with_no_matching_file_and_warns(self):
        import dataclasses
        deck = dataclasses.replace(self.deck, verb_order=(*self.deck.verb_order, "ghost"))

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            verbs = deck.load_verbs(Path("decks/pt/verbs"))

        self.assertNotIn("ghost", verbs)
        self.assertIn("'ghost'", stderr.getvalue())

    def test_tolerates_a_verb_file_not_listed_in_deck_yaml(self):
        import dataclasses
        verb_order = [lemma for lemma in self.deck.verb_order if lemma != "ter"]
        deck = dataclasses.replace(self.deck, verb_order=tuple(verb_order))

        verbs = deck.load_verbs(Path("decks/pt/verbs"))

        self.assertNotIn("ter", verbs)
        authored = [lemma for lemma in verb_order if lemma in verbs]
        self.assertEqual(list(verbs), authored)


if __name__ == "__main__":
    unittest.main()
