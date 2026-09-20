"""Loading of transformations supplied by an individual deck."""

from __future__ import annotations

import copy
import html
import importlib.util
import re
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

from kofiish.verb import Verb


Transformation = Callable[[str, Verb], Verb]
NotesFn = Callable[[str, Verb | None], dict[str, dict[str, str]]]


def irregular_note(wrong_form: str) -> str:
    """HTML note flagging a genuine irregularity against the naive guess.

    Use when the actual form has no rule behind it and must be memorized.
    ``wrong_form`` is the hypothetical *regular* form a learner would
    produce by naively applying the ending rules, e.g.
    ``irregular_note("quere")`` for ``querer``'s ``3sg`` (the real form,
    ``quer``, is already shown on the card).
    """
    return (
        '<span class="SECTION_regularity">'
        '<span class="note_feature">Irregular form</span>: the hypothetical '
        f'regular form <span class="wrong_conj">{wrong_form}</span> is '
        "incorrect.</span>"
    )


def _markup(text: str) -> str:
    body = html.escape(text.strip("\n"), quote=False)
    body = re.sub(r"`([^`]+)`", r'<span class="notes_sp_form">\1</span>', body)
    body = re.sub(r"\*([^*]+)\*", r'<span class="wrong_conj">\1</span>', body)
    body = re.sub(r"~([^~]+)~", r'<span class="note_spell">\1</span>', body)
    body = re.sub(r"\[\[(.+?)\]\]", r'<span class="note_feature">\1</span>', body)
    return body.replace("\n", "<br>")


def authored_note(text: str) -> str:
    """HTML for a note hand-written in a verb's YAML, styled like the helpers above.

    The text is plain prose with a light markup: `form` highlights a real
    Portuguese form or stem, *form* flags a wrong or naive guess, ~c → ç~
    marks a spelling change and [[irregular]] a feature of the verb, e.g.
    ``"`Faço` is [[irregular]] — not the expected *fazo*."``. A newline in
    the text starts a new line on the card.
    """
    return f'<span class="SECTION_regularity">{_markup(text)}</span>'


def form_note(
    ending: str,
    verb_class: str,
    on_infinitive: bool = False,
    spelling_change: tuple[str, str] | None = None,
) -> str:
    """HTML note naming a form's regular ending, and any regular spelling change.

    ``verb_class`` names the ending set, e.g. ``"-ar"``. ``on_infinitive``
    marks tenses built on the whole infinitive (futuro, condicional).
    ``spelling_change`` is the stem's ``(before, after)`` letters when a
    regular spelling rule changed them to preserve pronunciation, e.g.
    ``("g", "gu")`` for ``cheguei``.
    """
    body = _markup(f"`-{ending}` is the regular ending for verbs in ")
    body += f'<span class="note_spell">{html.escape(verb_class, quote=False)}</span>.'
    if spelling_change:
        change = html.escape(" → ".join(spelling_change), quote=False)
        body += (
            '<br>The <span class="note_feature">spelling change</span> '
            f'<span class="note_spell">{change}</span> is considered regular '
            "(preserves pronunciation)."
        )
    return f'<span class="SECTION_regularity">{body}</span>'


def conjugated_form_note(
    form: str | None,
    generated: str,
    ending: str,
    verb_class: str,
    on_infinitive: bool = False,
    spelling_change: tuple[str, str] | None = None,
) -> str | None:
    """A conjugator's note for the ``form`` shown on a card, where the
    conjugator itself produced ``generated`` from ``ending``.

    A verb's YAML can override the generated form. If the override still
    ends with the regular ending (pedir's ``peço``, ``durmo``), only the
    ending is noted: the stem change is the YAML's to explain, in its own
    note. An override that doesn't end with it (``pago``) gets no note.
    """
    if form == generated:
        return form_note(ending, verb_class, on_infinitive, spelling_change)
    if form and form.endswith(ending):
        return form_note(ending, verb_class, on_infinitive)
    return None


def stem_family(
    base_lemma: str,
    base_stem: str,
    base_forms: Verb,
    compound_forms: dict[tuple[str, str], str] | None = None,
) -> Transformation:
    """Build a transform for verbs that conjugate exactly like ``base_lemma``
    with a different stem.

    ``base_lemma`` is ``base_stem`` + a family ending (e.g. ``"v"`` + ``"er"``
    for ver, ``""`` + ``"ter"`` for ter), and every form in ``base_forms``
    starts with ``base_stem``. A lemma in the family must end with that same
    ending; its own stem replaces ``base_stem`` in every form
    (prever -> prevejo, crer -> creio, cair -> caímos, conter -> contenho).

    ``compound_forms`` replaces a base form, before the stem swap, for any
    lemma other than ``base_lemma`` itself: use it where the longer word needs
    a written accent the base form doesn't (tem -> contém, vem -> intervém).
    """
    ending = base_lemma[len(base_stem):]
    compound_forms = compound_forms or {}

    def transform(lemma: str, verb: Verb) -> Verb:
        if not lemma.endswith(ending):
            raise ValueError(
                f"{base_lemma!r} family only applies to verbs ending in {ending!r}, got: {lemma}"
            )

        stem = lemma[: len(lemma) - len(ending)]
        verb = copy.deepcopy(verb)
        for tense_name, forms in base_forms.items():
            resolved = {}
            for person, form in forms.items():
                if lemma != base_lemma:
                    form = compound_forms.get((tense_name, person), form)
                resolved[person] = stem + form[len(base_stem):]
            verb[tense_name].update(resolved)
        return verb

    return transform


class TransformationLoader:
    """Load named transformations from a deck's ``transformations`` directory."""

    def __init__(self, transformations_dir: Path) -> None:
        self.transformations_dir = transformations_dir
        self._modules: dict[str, ModuleType] = {}

    def load(self, name: str) -> Transformation:
        transformation = getattr(self._load_module(name), "transform", None)
        if not callable(transformation):
            raise ValueError(
                f"Transformation {name} must define a callable transform(lemma, verb)"
            )
        return transformation

    def load_notes(self, name: str) -> NotesFn | None:
        """Optional per-transformation `notes(lemma) -> {tense: {person: text}}`.

        Lets a transformation explain the forms shown on the cards, without
        every transformation having to define one. It's called as
        `notes(lemma, forms)`, where `forms` are the verb's final forms after
        the YAML overrides (``None`` means the transformation's own forms).
        A conjugator should give every form a note built with this module's
        `conjugated_form_note()`, naming the regular ending and any regular
        spelling change, rather than hand-writing the HTML — see
        `conjugator_ar.py`'s `notes()` for a worked example.
        """
        notes_fn = getattr(self._load_module(name), "notes", None)
        return notes_fn if callable(notes_fn) else None

    def _load_module(self, name: str) -> ModuleType:
        if name not in self._modules:
            path = self.transformations_dir / f"{name}.py"
            if not path.is_file():
                raise ValueError(f"Unknown transformation: {name}")

            module_name = f"kofiish_deck_transformation_{name}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ValueError(f"Could not load transformation: {name}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._modules[name] = module

        return self._modules[name]
