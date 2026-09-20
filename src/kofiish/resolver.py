"""Resolution stages that turn authored verb data into deck-ready data."""

from __future__ import annotations

import copy
import re

from kofiish.deck import Deck
from kofiish.transformation import TransformationLoader, authored_note
from kofiish.verb import ResolvedVerb, Verb, VerbDefinition


class VerbExpander:
    """Materialize every tense and form required by a deck.

    This is deliberately a factory rather than a transformation.  The result
    contains no authored data: it is only the complete shape prescribed by a
    deck.  Conjugators and later resolver stages can then fill that shape.
    """

    def __init__(self, deck: Deck) -> None:
        self.deck = deck

    def expand(self, lemma: str) -> Verb:
        # ``lemma`` identifies the verb being expanded, but is deliberately not
        # embedded in a morphological Verb. It belongs to ResolvedVerb metadata.
        return {
            tense_name: {form_name: None for form_name in tense_cfg.forms}
            for tense_name, tense_cfg in self.deck.tense_cfgs.items()
        }


class VerbResolver:
    """Resolve one lemma's forms: conjugate it, then overlay authored overrides.

    This is the single primitive for turning a lemma into its forms, and it
    is used identically whether the lemma is a verb's own or one of its
    analogs — an analog is just another lemma sharing the same
    transformations, with its own sparse overrides.
    """

    def __init__(self, expander: VerbExpander, transformation_loader: TransformationLoader) -> None:
        self.expander = expander
        self.transformation_loader = transformation_loader

    def resolve(self, lemma: str, transformations: tuple[str, ...], overrides: Verb) -> Verb:
        forms = self.expander.expand(lemma)
        for transformation_name in transformations:
            transformation = self.transformation_loader.load(transformation_name)
            forms = transformation(lemma, forms)

        resolved = copy.deepcopy(forms)
        for tense_name, tense_overrides in overrides.items():
            resolved.setdefault(tense_name, {}).update(tense_overrides)
        return resolved

    def resolve_notes(
        self, lemma: str, transformations: tuple[str, ...], forms: Verb | None = None
    ) -> dict[str, dict[str, str]]:
        """Notes the transformations give about `lemma`'s final `forms`
        (their own forms when ``None``)."""
        notes: dict[str, dict[str, str]] = {}
        for transformation_name in transformations:
            notes_fn = self.transformation_loader.load_notes(transformation_name)
            if notes_fn is None:
                continue
            for tense_name, tense_notes in notes_fn(lemma, forms).items():
                notes.setdefault(tense_name, {}).update(tense_notes)
        return notes


def _append_note(existing: str, note: str) -> str:
    """Show ``note`` on its own line after any note already on the card."""
    return f"{existing}<br>{note}" if existing else note


def _visible_text(note_html: str) -> str:
    return re.sub(r"<[^>]*>", "", note_html.replace("<br>", " "))


def resolve_verb(resolver: VerbResolver, source: VerbDefinition) -> ResolvedVerb:
    """Compose the compound object card generation and the CLI work from.

    The verb itself and each of its analogs are resolved independently,
    through ``VerbResolver.resolve``, before anything is combined here.
    """
    forms = resolver.resolve(source.lemma, source.transformations, source.forms)
    notes = resolver.resolve_notes(source.lemma, source.transformations, forms)
    for tense_name, tense_notes in source.notes.items():
        tense_resolved = notes.setdefault(tense_name, {})
        for person, text in tense_notes.items():
            # Shown after the transformation's note rather than replacing it;
            # an authored note reading the same as the generated one adds nothing.
            generated = tense_resolved.get(person, "")
            authored = authored_note(text)
            if _visible_text(authored) != _visible_text(generated):
                tense_resolved[person] = _append_note(generated, authored)
    # The tense's pattern comes last, after anything specific to the card.
    for tense_name, pattern in source.patterns.items():
        tense_resolved = notes.setdefault(tense_name, {})
        for person, form in forms.get(tense_name, {}).items():
            if form:
                tense_resolved[person] = _append_note(tense_resolved.get(person, ""), authored_note(pattern))
    analogs = {
        analog_lemma: resolver.resolve(analog_lemma, source.transformations, analog_overrides)
        for analog_lemma, analog_overrides in source.analogs.items()
    }

    return ResolvedVerb(
        lemma=source.lemma,
        translation=source.translation,
        forms=forms,
        contexts=copy.deepcopy(source.contexts),
        analogs=analogs,
        notes=notes,
    )
