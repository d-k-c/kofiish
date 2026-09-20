
import copy
from collections import Counter
import genanki
import json
import shutil
import tempfile
import unicodedata
import uuid
import zlib

from pathlib import Path
from urllib.parse import quote_plus

from kofiish.deck import Deck, DeckOptions
from kofiish.verb import ResolvedVerb, Verb


KOFIISH_NAMESPACE = uuid.UUID(bytes=b'KOFIANKIDECKUUID')

# All KOFI decks are for English-speaking learners; only the deck's own
# (source) language varies, via Deck.metadata.language.
TARGET_LANGUAGE = "english"


class PromptFormatter:

    FORMAT_TENSE = """<div class="{tense_name}">{cue}</div>"""
    FORMAT_PRONOUN = """<span class="cloze_pronoun">{pronoun}</span>"""
    FORMAT_VERB = """<span class="sp_verb">{{{{c1::{conjugate}::…{infinitive}…}}}}</span>"""
    FORMAT_HINT = """<span class="sp_hint">({hint})</span>"""
    FORMAT_PRONOUN_HINT = """<span class="pronoun_hint">({pronoun})</span>"""
    FORMAT_SIMILAR = """<span class="alt_conj">{conjugate}</span><span class="alt_to_inf">←</span><span class="alt_inf">{infinitive}</span>"""
    FORMAT_DICTIONARIES = """<span class="translation_title">Definition &amp; Translation: <span class="translate_me">{lemma}</span> ({translation})</span>"""
    FORMAT_SENTENCE_TRANSLATION = (
        '<a class="translation-other-languages" '
        'href="https://context.reverso.net/translation/{source_lang}-{target_lang}/{encoded}">'
        '<span class="translation_title">Translation for </span><span class="translate_me">{sentence}</span></a>'
    )

    @classmethod
    def format(
        cls,
        *,
        lemma,
        conjugated_form,
        pronoun,
        pronoun_as_hint=False,
        tense_name,
        tense_visual_cue,
        context_cue,
        hint,
    ):
        header_cue = context_cue or ""
        if tense_visual_cue:
            header_cue = f"{tense_visual_cue} {header_cue} {tense_visual_cue}"

        s = cls.FORMAT_TENSE.format(tense_name=tense_name, cue=header_cue)
        s += "<br>"

        if pronoun and not pronoun_as_hint:
            s += cls.FORMAT_PRONOUN.format(pronoun=pronoun)
            s += " "

        s += cls.FORMAT_VERB.format(conjugate=conjugated_form, infinitive=lemma)

        if hint:
            s += " " + cls.FORMAT_HINT.format(hint=hint)

        if pronoun and pronoun_as_hint:
            s += "<br><br>" + cls.FORMAT_PRONOUN_HINT.format(pronoun=pronoun)

        return s

    @classmethod
    def format_similar(cls, analogs: dict[str, Verb], tense_name: str, form_name: str) -> str:
        return "<br>".join(
            cls.FORMAT_SIMILAR.format(conjugate=form, infinitive=analog_lemma)
            for analog_lemma, analog_forms in analogs.items()
            if (form := analog_forms.get(tense_name, {}).get(form_name))
        )

    @classmethod
    def format_dictionaries(cls, *, lemma: str, translation: str) -> str:
        return cls.FORMAT_DICTIONARIES.format(lemma=lemma, translation=translation)

    @classmethod
    def format_plain_sentence(
        cls,
        *,
        conjugated_form: str,
        pronoun: str | None,
        pronoun_as_hint: bool,
        context_cue: str | None,
        hint: str | None,
    ) -> str:
        """The card's sentence as plain text (no cue-header markup, no cloze)."""
        sentence = f"{context_cue} " if context_cue else ""
        if pronoun and not pronoun_as_hint:
            sentence += f"{pronoun} "
        sentence += conjugated_form
        if hint:
            sentence += f" {hint}"
        if pronoun and pronoun_as_hint:
            sentence += f" ({pronoun})"
        return sentence

    @classmethod
    def format_sentence_translation(cls, *, sentence: str, source_lang: str, target_lang: str) -> str:
        return cls.FORMAT_SENTENCE_TRANSLATION.format(
            sentence=sentence,
            source_lang=source_lang,
            target_lang=target_lang,
            encoded=quote_plus(sentence),
        )


def spoken_text(deck: Deck, lemma: str, tense_name: str, form_name: str, conjugated_form: str) -> str:
    """What a card's recording says: its form, led by the pronoun.

    The pronoun gives the ear a lead-in to the form. Tenses that show the
    pronoun only as a hint (the imperatives) and impersonal forms stay bare.
    A prompt offering alternatives, e.g. "ele | ela", uses one of them per
    card, picked by a stable hash so the deck hears a mix of both.
    """
    tense_cfg = deck.tense_cfgs[tense_name]
    pronoun = tense_cfg.pronoun_for(form_name, deck.pronouns)
    if not pronoun or tense_cfg.pronoun_hint:
        return conjugated_form

    alternatives = [alternative.strip() for alternative in pronoun.split("|")]
    pick = zlib.crc32(f"{lemma}|{tense_name}|{form_name}".encode()) % len(alternatives)
    return f"{alternatives[pick]} {conjugated_form}"


class PronunciationMedia:
    """Optional mp3 recordings of what a deck's cards say (see spoken_text).

    A recording lives at ``<deck>/media/<lemma>/<spoken text>.mp3`` and is
    shared by every cell saying the same thing. Anki keeps all media in one
    flat folder, so each file is published under a name unique across decks,
    e.g. ``kofi_pt_fazer_eu_faço.mp3``. A card without a recording gets no
    audio.

    Accented names may be stored composed or decomposed on disk (macOS tools
    often write decomposed ones), so files are matched by their NFC-normalized
    name rather than by building a path; published names are NFC, as Anki
    stores them.
    """

    def __init__(self, deck_dir: Path) -> None:
        self.media_dir = deck_dir / "media"
        self.prefix = f"kofiish_{deck_dir.name}"
        self._recordings: dict[str, dict[str, Path]] = {}

    def published_name(self, lemma: str, form: str) -> str:
        return f"{self.prefix}_{_nfc(lemma)}_{_nfc(form).replace(' ', '_')}.mp3"

    def find(self, lemma: str, form: str) -> tuple[Path, str] | None:
        """The recording's source path and published name, if one exists."""
        path = self._recordings_for(lemma).get(_nfc(f"{form}.mp3"))
        if path is None:
            return None
        return path, self.published_name(lemma, form)

    def target_path(self, lemma: str, form: str) -> Path:
        """Where a new recording of ``form`` should be written.

        Reuses the lemma's folder if one exists under any normalization,
        so a recording never lands in a duplicate, differently-encoded folder.
        """
        lemma_dirs = self._lemma_dirs(lemma)
        lemma_dir = lemma_dirs[0] if lemma_dirs else self.media_dir / _nfc(lemma)
        return lemma_dir / _nfc(f"{form}.mp3")

    def _lemma_dirs(self, lemma: str) -> list[Path]:
        return [
            path for path in _entries(self.media_dir)
            if path.is_dir() and _nfc(path.name) == _nfc(lemma)
        ]

    def _recordings_for(self, lemma: str) -> dict[str, Path]:
        """NFC file name -> path, for every file in the lemma's folder."""
        if lemma not in self._recordings:
            lemma_dirs = self._lemma_dirs(lemma)
            self._recordings[lemma] = {
                _nfc(path.name): path
                for lemma_dir in lemma_dirs
                for path in _entries(lemma_dir)
                if path.is_file()
            }
        return self._recordings[lemma]


def _entries(directory: Path) -> list[Path]:
    return list(directory.iterdir()) if directory.is_dir() else []


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


class OptionsPackage(genanki.Package):
    """A package whose decks use their own options preset.

    genanki attaches every deck to Anki's "Default" preset (id 1). This adds
    ``options`` as a second preset, a copy of genanki's Default with the
    deck's settings applied, and points the decks at it.
    """

    def __init__(self, deck_or_decks, media_files, options: DeckOptions) -> None:
        super().__init__(deck_or_decks, media_files=media_files)
        self.options = options

    def write_to_db(self, cursor, timestamp: float, id_gen) -> None:
        super().write_to_db(cursor, timestamp, id_gen)
        dconf_json, decks_json = cursor.execute("SELECT dconf, decks FROM col").fetchone()
        dconf, decks = json.loads(dconf_json), json.loads(decks_json)

        preset = copy.deepcopy(dconf["1"])
        preset.update(
            id=self.options.id,
            name=self.options.name,
            mod=int(timestamp),
            desiredRetention=self.options.desired_retention,
        )
        preset["new"].update(
            perDay=self.options.new_per_day,
            delays=list(self.options.learning_steps),
            order=DeckOptions.NEW_CARD_ORDERS.index(self.options.new_card_order),
        )
        preset["rev"].update(perDay=self.options.reviews_per_day, maxIvl=self.options.maximum_interval)
        preset["lapse"].update(
            delays=list(self.options.relearning_steps),
            leechFails=self.options.leech_threshold,
        )
        dconf[str(self.options.id)] = preset

        for deck in self.decks:
            decks[str(deck.deck_id)]["conf"] = self.options.id

        cursor.execute("UPDATE col SET dconf = ?, decks = ?", (json.dumps(dconf), json.dumps(decks)))


class AnkiDeck:

    def __init__(
        self,
        deck: Deck,
        verbs: dict[str, ResolvedVerb],
        deck_dir: Path,
    ) -> "Self":
        self.kofi_deck = deck
        self.verbs = verbs
        self.pronunciation = PronunciationMedia(deck_dir)
        # published name -> source path, for every recording a card uses
        self.media_files: dict[str, Path] = {}
        # lemma -> number of cards generated for it
        self.card_counts: Counter[str] = Counter()

        assets_path = deck_dir / "assets"

        with open(assets_path / "front-template", "r", encoding="utf-8") as file:
            self.front_template = file.read()

        with open(assets_path / "back-template", "r", encoding="utf-8") as file:
            self.back_template = file.read()

        with open(assets_path / "styling", "r", encoding="utf-8") as file:
            self.style = file.read()

        self.model = genanki.Model(
            deck.metadata.model.id,
            deck.metadata.model.name,
            fields=[
                {'name': 'UUID'},
                {'name': 'Prompt'},
                *[{'name': f} for f in deck.fields]
            ],
            templates=[
                {
                    'name': 'Cloze',
                    'qfmt': self.front_template,
                    'afmt': self.back_template,
                },
            ],
            css=self.style,
            model_type=genanki.Model.CLOZE,
            sort_field_index=1,
        )

        self.deck = genanki.Deck(
            deck.metadata.deck.id,
            deck.metadata.deck.name,
        )


    def get_uuid(self, tags) -> str:
        return uuid.uuid5(KOFIISH_NAMESPACE, '|'.join(tags)).hex


    def generate_card(
        self,
        verb: ResolvedVerb,
        tense_name: str,
        form_name: str,
    ) -> None:
        conjugated_form = verb.forms[tense_name][form_name]
        if not conjugated_form:
            return

        context = verb.get_context(tense_name, form_name)
        tense_cfg = self.kofi_deck.tense_cfgs[tense_name]

        pronoun = tense_cfg.pronoun_for(form_name, self.kofi_deck.pronouns)
        pronoun_tag = self.kofi_deck.pronouns[form_name].get_tag()
        if pronoun_tag:
            tags = [tense_name, verb.lemma, pronoun_tag]
        else:
            tags = [tense_name, verb.lemma]

        uuid = self.get_uuid(tags)

        prompt = PromptFormatter.format(
            lemma=verb.lemma,
            conjugated_form=conjugated_form,
            pronoun=pronoun,
            pronoun_as_hint=tense_cfg.pronoun_hint,
            tense_name=tense_name,
            tense_visual_cue=tense_cfg.cue,
            context_cue=context.cue,
            hint=context.hint,
        )

        field_values = {f: '' for f in self.kofi_deck.fields}

        similar = PromptFormatter.format_similar(verb.analogs, tense_name, form_name)
        if 'Similar' in field_values:
            field_values['Similar'] = similar

        note_text = verb.get_note(tense_name, form_name)
        if note_text and 'Notes' in field_values:
            field_values['Notes'] = note_text

        if 'Dictionaries' in field_values:
            field_values['Dictionaries'] = PromptFormatter.format_dictionaries(
                lemma=verb.lemma,
                translation=verb.translation,
            )

        if 'Pronunciation' in field_values:
            spoken = spoken_text(self.kofi_deck, verb.lemma, tense_name, form_name, conjugated_form)
            recording = self.pronunciation.find(verb.lemma, spoken)
            if recording:
                source_path, published_name = recording
                self.media_files[published_name] = source_path
                field_values['Pronunciation'] = f'[sound:{published_name}]'

        if 'Sentence_Translation' in field_values:
            plain_sentence = PromptFormatter.format_plain_sentence(
                conjugated_form=conjugated_form,
                pronoun=pronoun,
                pronoun_as_hint=tense_cfg.pronoun_hint,
                context_cue=context.cue,
                hint=context.hint,
            )
            field_values['Sentence_Translation'] = PromptFormatter.format_sentence_translation(
                sentence=plain_sentence,
                source_lang=self.kofi_deck.metadata.language,
                target_lang=TARGET_LANGUAGE,
            )

        note = genanki.Note(
            model=self.model,
            fields=[uuid, prompt, *[field_values[f] for f in self.kofi_deck.fields]],
            tags=tags,
            # Identity comes from tense/verb/person, not field content, so
            # editing a card's text updates it in place on reimport.
            guid=uuid,
        )

        self.deck.add_note(note)
        self.card_counts[verb.lemma] += 1

    def description(self) -> str:
        """The deck's description: its verbs in deck order, with their card counts.

        New cards aren't introduced automatically (the options preset sets
        0 per day), so this tells the learner how many cards each verb adds.
        """
        lemmas = [lemma for lemma in self.kofi_deck.verb_order if self.card_counts[lemma]]
        width = len(str(len(lemmas)))
        return "\n".join(
            f"{number:0{max(width, 2)}}. {lemma} ({self.card_counts[lemma]} cards)"
            for number, lemma in enumerate(lemmas, start=1)
        )

    def write(
        self,
        out_path: Path,
        selections: list[tuple[ResolvedVerb, str, str]] | None = None,
    ) -> None:
        if selections is None:
            selections = [
                (verb, tense_name, form_name)
                for verb in self.verbs.values()
                for tense_name, tense_data in self.kofi_deck.tense_cfgs.items()
                for form_name in tense_data.forms
            ]

        for verb, tense_name, form_name in selections:
            self.generate_card(verb, tense_name, form_name)
        self.deck.description = self.description()

        # genanki names each media file after its path's basename, so stage
        # the recordings under their published names first.
        with tempfile.TemporaryDirectory() as staging:
            staged = []
            for published_name, source_path in self.media_files.items():
                staged_path = Path(staging) / published_name
                shutil.copyfile(source_path, staged_path)
                staged.append(str(staged_path))
            options = self.kofi_deck.metadata.options
            if options:
                package = OptionsPackage(self.deck, staged, options)
            else:
                package = genanki.Package(self.deck, media_files=staged)
            package.write_to_file(out_path)

        print("Deck generated:", out_path)
        if 'Pronunciation' in self.kofi_deck.fields:
            print(f"Pronunciation recordings: {len(self.media_files)}")
