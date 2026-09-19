
import genanki
import uuid

from pathlib import Path

from kofiish.deck import Deck


KOFIISH_NAMESPACE = uuid.UUID(bytes=b'KOFIANKIDECKUUID')

class PromptFormatter:

    FORMAT_TENSE = """<div class="{tense_name}">{cue}</div>"""
    FORMAT_PRONOUN = """<span class="cloze_pronoun">{pronoun}</span>"""
    FORMAT_VERB = """<span class="sp_verb">{{{{c1::{conjugate}::…{infinitive}…}}}}</span>"""
    FORMAT_HINT = """<span class="sp_hint">({hint})</span>"""

    @classmethod
    def format(cls, lemma, conjugated_form, pronoun, tense_name, tense_visual_cue, cue, hint):
        if tense_visual_cue:
            cue = tense_visual_cue + " " + cue + " " + tense_visual_cue

        s = cls.FORMAT_TENSE.format(tense_name=tense_name, cue=cue)
        s += "<br>"

        if pronoun:
            s += cls.FORMAT_PRONOUN.format(pronoun=pronoun)
            s += " "

        s += cls.FORMAT_VERB.format(conjugate=conjugated_form, infinitive=lemma)

        if hint:
            s += " " + cls.FORMAT_HINT.format(hint=hint)

        return s


class AnkiDeck:

    def __init__(self, deck: Deck, deck_dir: Path) -> "Self":
        self.kofi_deck = deck

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


    def generate_card(self, verb, tense_name, form_name):
        conjugated_form_ctx = verb.tenses[tense_name][form_name]
        if not conjugated_form_ctx.form:
            return

        pronoun = self.kofi_deck.pronouns[form_name].prompt
        pronoun_tag = self.kofi_deck.pronouns[form_name].get_tag()
        if pronoun_tag:
            tags = [tense_name, verb.lemma, pronoun_tag]
        else:
            tags = [tense_name, verb.lemma]

        uuid = self.get_uuid(tags)

        prompt = PromptFormatter.format(verb.lemma,
                                        conjugated_form_ctx.form,
                                        pronoun,
                                        tense_name,
                                        self.kofi_deck.tenses[tense_name].cue,
                                        conjugated_form_ctx.context.cue,
                                        conjugated_form_ctx.context.hint)

        note = genanki.Note(
            model=self.model,
            fields=[uuid, prompt, *['' for f in self.kofi_deck.fields]],
            tags=tags,
        )

        self.deck.add_note(note)

    def write(self, out_path: Path) -> None:
        for verb in self.kofi_deck.verbs.values():
            for tense_name, tense_data in self.kofi_deck.tenses.items():
                for form_name in tense_data.forms:
                    self.generate_card(verb, tense_name, form_name)

        genanki.Package(self.deck).write_to_file(out_path)
        print("Deck generated:", out_path)
