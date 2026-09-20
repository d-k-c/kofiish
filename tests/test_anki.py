import copy
import json
import sqlite3
import unicodedata
import tempfile
import unittest
import zipfile
from pathlib import Path

from kofiish.anki import AnkiDeck, PromptFormatter, PronunciationMedia, spoken_text
from kofiish.main import load_resolved_verbs


class FormatDictionariesTests(unittest.TestCase):
    def test_matches_the_definition_and_translation_template(self):
        result = PromptFormatter.format_dictionaries(lemma="ficar", translation="to stay / to become")

        self.assertEqual(
            result,
            '<span class="translation_title">Definition &amp; Translation: '
            '<span class="translate_me">ficar</span> (to stay / to become)</span>',
        )


class FormatPlainSentenceTests(unittest.TestCase):
    def test_combines_cue_pronoun_form_and_hint(self):
        sentence = PromptFormatter.format_plain_sentence(
            conjugated_form="fico",
            pronoun="eu",
            pronoun_as_hint=False,
            context_cue="Hoje,",
            hint="em casa",
        )

        self.assertEqual(sentence, "Hoje, eu fico em casa")

    def test_puts_the_pronoun_in_parentheses_after_when_used_as_a_hint(self):
        sentence = PromptFormatter.format_plain_sentence(
            conjugated_form="fica",
            pronoun="você",
            pronoun_as_hint=True,
            context_cue="Por favor,",
            hint="por aqui",
        )

        self.assertEqual(sentence, "Por favor, fica por aqui (você)")

    def test_omits_cue_and_hint_when_absent(self):
        sentence = PromptFormatter.format_plain_sentence(
            conjugated_form="fico",
            pronoun=None,
            pronoun_as_hint=False,
            context_cue=None,
            hint=None,
        )

        self.assertEqual(sentence, "fico")


class FormatSentenceTranslationTests(unittest.TestCase):
    def test_wraps_the_whole_translation_for_phrase_in_a_single_link(self):
        result = PromptFormatter.format_sentence_translation(
            sentence="Hoje, eu fico em casa",
            source_lang="portuguese",
            target_lang="english",
        )

        self.assertEqual(
            result,
            '<a class="translation-other-languages" '
            'href="https://context.reverso.net/translation/portuguese-english/'
            'Hoje%2C+eu+fico+em+casa">'
            '<span class="translation_title">Translation for </span>'
            '<span class="translate_me">Hoje, eu fico em casa</span></a>',
        )

    def test_url_encodes_spaces_as_plus_and_keeps_punctuation(self):
        result = PromptFormatter.format_sentence_translation(
            sentence="Allez-y croissez rapidement.",
            source_lang="french",
            target_lang="english",
        )

        self.assertIn(
            'href="https://context.reverso.net/translation/french-english/'
            'Allez-y+croissez+rapidement."',
            result,
        )


if __name__ == "__main__":
    unittest.main()


class NoteGuidTests(unittest.TestCase):
    def test_guid_is_the_stable_uuid_not_a_hash_of_the_content(self):
        deck_dir, deck, verbs = load_resolved_verbs("pt")
        edited = copy.deepcopy(verbs["fazer"])
        edited.notes["presente_indicativo"]["1sg"] = "a different note"

        guids = []
        for verb in (verbs["fazer"], edited):
            anki_deck = AnkiDeck(deck, {"fazer": verb}, deck_dir)
            anki_deck.generate_card(verb, "presente_indicativo", "1sg")
            note = anki_deck.deck.notes[0]
            self.assertEqual(note.guid, note.fields[0])
            guids.append(note.guid)

        self.assertEqual(guids[0], guids[1])


class DeckOptionsTests(unittest.TestCase):
    def setUp(self):
        self.deck_dir, self.deck, self.verbs = load_resolved_verbs("pt")
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def packaged_col(self, deck):
        out_path = Path(self.tmp.name) / "out.apkg"
        anki_deck = AnkiDeck(deck, self.verbs, self.deck_dir)
        anki_deck.write(out_path, [(self.verbs["ter"], "presente_indicativo", "1sg")])
        db_path = Path(self.tmp.name) / "collection.anki2"
        with zipfile.ZipFile(out_path) as package:
            db_path.write_bytes(package.read("collection.anki2"))
        connection = sqlite3.connect(db_path)
        try:
            dconf, decks = connection.execute("SELECT dconf, decks FROM col").fetchone()
        finally:
            connection.close()
        return json.loads(dconf), json.loads(decks)

    def test_deck_uses_its_options_preset(self):
        options = self.deck.metadata.options
        dconf, decks = self.packaged_col(self.deck)

        self.assertEqual(decks[str(self.deck.metadata.deck.id)]["conf"], options.id)
        preset = dconf[str(options.id)]
        self.assertEqual(preset["name"], "KOFI Portuguese")
        self.assertEqual(preset["new"]["perDay"], 0)
        self.assertEqual(preset["new"]["delays"], [15])
        self.assertEqual(preset["new"]["order"], 1)
        self.assertEqual(preset["rev"]["perDay"], 9999)
        self.assertEqual(preset["rev"]["maxIvl"], 1826)
        self.assertEqual(preset["lapse"]["delays"], [15])
        self.assertEqual(preset["lapse"]["leechFails"], 9999)
        self.assertEqual(preset["desiredRetention"], 0.9)
        # the rest is genanki's complete Default, which stays untouched
        self.assertEqual(preset["new"]["ints"], dconf["1"]["new"]["ints"])
        self.assertEqual(dconf["1"]["new"]["perDay"], 20)

    def test_deck_without_options_keeps_the_default_preset(self):
        deck = copy.deepcopy(self.deck)
        deck.metadata = copy.replace(deck.metadata, options=None)
        dconf, decks = self.packaged_col(deck)

        self.assertEqual(list(dconf), ["1"])
        self.assertEqual(decks[str(self.deck.metadata.deck.id)]["conf"], 1)


class DeckDescriptionTests(unittest.TestCase):
    def test_lists_verbs_in_deck_order_with_their_card_count(self):
        deck_dir, deck, verbs = load_resolved_verbs("pt")
        anki_deck = AnkiDeck(deck, verbs, deck_dir)
        selections = [
            (verbs["ser"], "presente_indicativo", "1sg"),
            (verbs["ser"], "presente_indicativo", "2sg"),
            (verbs["ter"], "gerundio", "all"),
        ]
        for selection in selections:
            anki_deck.generate_card(*selection)

        self.assertEqual(anki_deck.description(), "01. ter (1 cards)\n02. ser (2 cards)")


class PronunciationTests(unittest.TestCase):
    def setUp(self):
        self.deck_dir, self.deck, self.verbs = load_resolved_verbs("pt")
        self.tmp = tempfile.TemporaryDirectory()
        # a stand-in deck dir named "pt", holding only the media folder
        self.media_deck_dir = Path(self.tmp.name) / "pt"
        (self.media_deck_dir / "media" / "fazer").mkdir(parents=True)
        (self.media_deck_dir / "media" / "fazer" / "eu fazia.mp3").write_bytes(b"fazia-audio")

        self.anki_deck = AnkiDeck(self.deck, self.verbs, self.deck_dir)
        self.anki_deck.pronunciation = PronunciationMedia(self.media_deck_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def pronunciation_field(self, note):
        return note.fields[2 + self.deck.fields.index("Pronunciation")]

    def test_a_card_plays_its_pronoun_and_form(self):
        self.anki_deck.generate_card(self.verbs["fazer"], "preterito_imperfeito_indicativo", "1sg")

        self.assertEqual(
            self.pronunciation_field(self.anki_deck.deck.notes[0]), "[sound:kofi_pt_fazer_eu_fazia.mp3]"
        )
        self.assertEqual(list(self.anki_deck.media_files), ["kofi_pt_fazer_eu_fazia.mp3"])

    def test_a_form_without_a_recording_gets_no_audio(self):
        self.anki_deck.generate_card(self.verbs["fazer"], "presente_indicativo", "1sg")

        self.assertEqual(self.pronunciation_field(self.anki_deck.deck.notes[0]), "")
        self.assertEqual(self.anki_deck.media_files, {})

    def test_recordings_are_packaged_under_their_published_name(self):
        out_path = Path(self.tmp.name) / "out.apkg"
        self.anki_deck.write(out_path, [(self.verbs["fazer"], "preterito_imperfeito_indicativo", "1sg")])

        with zipfile.ZipFile(out_path) as package:
            media = json.loads(package.read("media"))
            self.assertEqual(list(media.values()), ["kofi_pt_fazer_eu_fazia.mp3"])
            (index,) = media
            self.assertEqual(package.read(index), b"fazia-audio")

    def test_finds_a_recording_saved_under_a_decomposed_name(self):
        lemma_dir = self.media_deck_dir / "media" / unicodedata.normalize("NFD", "começar")
        lemma_dir.mkdir()
        (lemma_dir / unicodedata.normalize("NFD", "eu começo.mp3")).write_bytes(b"")

        self.anki_deck.generate_card(self.verbs["começar"], "presente_indicativo", "1sg")

        published_name = unicodedata.normalize("NFC", "kofi_pt_começar_eu_começo.mp3")
        self.assertEqual(
            self.pronunciation_field(self.anki_deck.deck.notes[0]), f"[sound:{published_name}]"
        )
        self.assertEqual(list(self.anki_deck.media_files), [published_name])

    def test_published_name_is_flat_and_space_free(self):
        media = PronunciationMedia(self.media_deck_dir)
        self.assertEqual(media.published_name("chamar-se", "me chame"), "kofi_pt_chamar-se_me_chame.mp3")


class SpokenTextTests(unittest.TestCase):
    def setUp(self):
        _, self.deck, self.verbs = load_resolved_verbs("pt")

    def spoken(self, lemma, tense_name, form_name):
        form = self.verbs[lemma].forms[tense_name][form_name]
        return spoken_text(self.deck, lemma, tense_name, form_name, form)

    def test_leads_with_the_pronoun(self):
        self.assertEqual(self.spoken("fazer", "presente_indicativo", "1sg"), "eu faço")
        self.assertEqual(self.spoken("fazer", "infinitivo_pessoal", "2sg"), "tu fazeres")

    def test_subjunctives_have_no_conjunction(self):
        self.assertEqual(self.spoken("fazer", "presente_conjuntivo", "1sg"), "eu faça")
        self.assertEqual(self.spoken("chamar-se", "futuro_conjuntivo", "1sg"), "eu me chamar")

    def test_imperatives_and_impersonal_forms_are_bare(self):
        self.assertEqual(self.spoken("fazer", "imperativo_afirmativo", "2sg"), "faz")
        self.assertEqual(self.spoken("fazer", "imperativo_negativo", "3sg"), "faça")
        self.assertEqual(self.spoken("fazer", "gerundio", "all"), "fazendo")

    def test_alternative_pronouns_are_both_used_across_the_deck(self):
        third_persons = [
            word
            for lemma in self.verbs
            for tense_name, tense_cfg in self.deck.tense_cfgs.items()
            if "3sg" in tense_cfg.forms and not tense_cfg.pronoun_hint
            for word in self.spoken(lemma, tense_name, "3sg").split()
            if word in ("ele", "ela")
        ]
        self.assertEqual(set(third_persons), {"ele", "ela"})
