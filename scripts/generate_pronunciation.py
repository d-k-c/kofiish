"""Generate a verb's pronunciation mp3s with Google Cloud Text-to-Speech.

One recording per distinct thing the verb's cards say (the form led by its
pronoun, see kofiish.anki.spoken_text), written where the deck build picks
it up: ``decks/<deck>/media/<lemma>/<spoken text>.mp3``. Recordings that
already exist are skipped unless --overwrite is given, since every request
is billed.

Run from the repository root:

    uv run --extra tts python scripts/generate_pronunciation.py pt fazer
    uv run --extra tts python scripts/generate_pronunciation.py pt fazer --form faço --form fiz

Authenticates through Application Default Credentials, e.g. after
``gcloud auth application-default login``.

Forms listed in ``decks/<deck>/pronunciation.yaml`` are synthesized from their
IPA with an SSML ``<phoneme>`` tag, for forms the voice gets wrong from the
spelling alone. After adding one, regenerate it with --overwrite --form.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import yaml

from kofiish.anki import PronunciationMedia, spoken_text
from kofiish.deck import Deck
from kofiish.main import load_resolved_verbs
from kofiish.verb import ResolvedVerb


LANGUAGE_CODE = "pt-PT"
DEFAULT_VOICE = "pt-PT-Wavenet-E"


def recordings(deck: Deck, verb: ResolvedVerb) -> dict[str, str]:
    """Spoken text -> the form it ends with, once each, in deck order."""
    spoken = {}
    for tense_name, tense_cfg in deck.tense_cfgs.items():
        for form_name in tense_cfg.forms:
            form = verb.forms[tense_name][form_name]
            if form:
                spoken.setdefault(spoken_text(deck, verb.lemma, tense_name, form_name, form), form)
    return spoken


def load_ipa(deck_dir: Path) -> dict[str, str]:
    """IPA overrides keyed by NFC-normalized form; empty if the deck has none."""
    path = deck_dir / "pronunciation.yaml"
    if not path.exists():
        return {}
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {_nfc(form): ipa for form, ipa in entries.items()}


def select_recordings(deck: Deck, verb: ResolvedVerb, requested: list[str] | None) -> dict[str, str]:
    """The verb's recordings, or only those of the ``requested`` forms."""
    spoken = recordings(deck, verb)
    if not requested:
        return spoken

    requested_nfc = {_nfc(form) for form in requested}
    unknown = requested_nfc - {_nfc(form) for form in spoken.values()}
    if unknown:
        raise ValueError(f"Not a form of {verb.lemma}: {', '.join(sorted(unknown))}")
    return {text: form for text, form in spoken.items() if _nfc(form) in requested_nfc}


def synthesize(client, voice: str, text: str, form: str, ipa: str | None) -> bytes:
    """Speak ``text``, which ends with ``form``, reading ``form`` as ``ipa`` if given."""
    from google.cloud import texttospeech

    if ipa is None:
        synthesis_input = texttospeech.SynthesisInput(text=text)
    else:
        lead_in = escape(text[: len(text) - len(form)])
        ssml = f'<speak>{lead_in}<phoneme alphabet="ipa" ph={quoteattr(ipa)}>{escape(form)}</phoneme></speak>'
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, name=voice),
        audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3),
    )
    return response.audio_content


def describe(text: str, form: str, ipa: dict[str, str]) -> str:
    override = ipa.get(_nfc(form))
    return f"{text} [{override}]" if override else text


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("deck_name", help="name of the deck, e.g. pt")
    parser.add_argument("lemma", help="verb infinitive")
    parser.add_argument(
        "--form",
        action="append",
        dest="forms",
        help="only the recordings of this conjugated form (repeatable); defaults to every form",
    )
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"default: {DEFAULT_VOICE}")
    parser.add_argument("--overwrite", action="store_true", help="regenerate existing recordings")
    parser.add_argument("--dry-run", action="store_true", help="list what would be generated")
    args = parser.parse_args()

    deck_dir, deck, verbs = load_resolved_verbs(args.deck_name)
    if args.lemma not in verbs:
        parser.error(f"Unknown verb for deck {args.deck_name}: {args.lemma}")
    try:
        selected = select_recordings(deck, verbs[args.lemma], args.forms)
    except ValueError as error:
        parser.error(str(error))

    media = PronunciationMedia(deck_dir)
    ipa = load_ipa(deck_dir)
    todo = {
        text: form for text, form in selected.items()
        if args.overwrite or not media.find(args.lemma, text)
    }
    print(f"{args.lemma}: {len(todo)} to generate, {len(selected) - len(todo)} already recorded")
    if args.dry_run or not todo:
        for text, form in todo.items():
            print(f"  {describe(text, form, ipa)} -> {media.target_path(args.lemma, text)}")
        return 0

    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    for text, form in todo.items():
        path = media.target_path(args.lemma, text)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(synthesize(client, args.voice, text, form, ipa.get(_nfc(form))))
        print(f"  {describe(text, form, ipa)} -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
