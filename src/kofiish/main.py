import argparse
from itertools import groupby
from pathlib import Path

from kofiish.anki import AnkiDeck, PronunciationMedia, spoken_text
from kofiish.deck import Deck, DeckLoader
from kofiish.resolver import VerbExpander, VerbResolver, resolve_verb
from kofiish.transformation import TransformationLoader
from kofiish.verb import ResolvedVerb


DECKS_DIR = Path("decks")


def list_decks() -> None:
    print("Available decks:")
    for path in sorted(DECKS_DIR.iterdir()):
        if path.is_dir() and (path / "deck.yaml").exists():
            print("\t- " + path.name)


def load_resolved_verbs(deck_name: str) -> tuple[Path, Deck, dict[str, ResolvedVerb]]:
    deck_dir = DECKS_DIR / deck_name
    deck_path = deck_dir / "deck.yaml"

    if not deck_path.exists():
        raise ValueError(f"Unknown deck: {deck_name}")

    deck = DeckLoader().load(deck_path)
    verb_definitions = deck.load_verbs(deck_dir / "verbs")

    expander = VerbExpander(deck)
    transformation_loader = TransformationLoader(deck_dir / "transformations")
    resolver = VerbResolver(expander, transformation_loader)

    resolved_verbs = {
        lemma: resolve_verb(resolver, source_verb)
        for lemma, source_verb in verb_definitions.items()
    }

    return deck_dir, deck, resolved_verbs


def build_deck(deck_name: str, output: Path | None = None) -> None:
    deck_dir, deck, resolved_verbs = load_resolved_verbs(deck_name)
    anki = AnkiDeck(deck, resolved_verbs, deck_dir)

    anki.write(output or Path("kofiish_" + deck_name + ".apkg"))


def select_forms(
    deck,
    verb: ResolvedVerb,
    tense: str | None,
    person: str | None,
) -> list[tuple[ResolvedVerb, str, str]]:
    if tense and tense not in deck.tense_cfgs:
        raise ValueError(f"Unknown tense: {tense}")

    selections = []
    tense_names = (tense,) if tense else deck.tense_cfgs
    for tense_name in tense_names:
        tense_cfg = deck.tense_cfgs[tense_name]
        if person:
            if person not in tense_cfg.forms:
                if tense:
                    raise ValueError(f"{person} is not available for {tense_name}")
                continue
            form_names = (person,)
        else:
            form_names = tense_cfg.forms

        for form_name in form_names:
            if verb.forms[tense_name][form_name]:
                selections.append((verb, tense_name, form_name))
    return selections


FORM_COLUMN_WIDTH = 5  # every form name (1sg, all, ...) is short and uniform
SUBLINE_LABEL_WIDTH = 8  # aligns "context"/"analogs"/"audio" under each other


def print_forms(
    deck,
    selections,
    include_context: bool,
    include_analogs: bool,
    media: PronunciationMedia | None = None,
) -> None:
    indent = " " * (FORM_COLUMN_WIDTH + 3)  # 2-space left margin + form column + 1 separator

    for verb, verb_selections in groupby(selections, key=lambda selection: selection[0]):
        print(verb.lemma)
        for tense_name, tense_selections in groupby(
            verb_selections,
            key=lambda selection: selection[1],
        ):
            tense_cfg = deck.tense_cfgs[tense_name]
            header = tense_name if not tense_cfg.cue else f"{tense_name} {tense_cfg.cue}"
            print(f"\n  {header}")

            for _, _, form_name in tense_selections:
                form = verb.forms[tense_name][form_name]
                print(f"  {form_name:<{FORM_COLUMN_WIDTH}} {form}")

                if include_context:
                    context = verb.get_context(tense_name, form_name)
                    pronoun = tense_cfg.pronoun_for(form_name, deck.pronouns)

                    prompt = (context.cue + " ") if context.cue else ''
                    if pronoun and not tense_cfg.pronoun_hint:
                        prompt += pronoun + " "
                    prompt += form
                    prompt += " " + context.hint if context.hint else ''
                    if pronoun and tense_cfg.pronoun_hint:
                        prompt += f" ({pronoun})"

                    print(f"{indent}{'context':<{SUBLINE_LABEL_WIDTH}} {prompt}")

                if include_analogs:
                    analog_forms = [
                        analog_forms[tense_name][form_name]
                        for analog_forms in verb.analogs.values()
                        if analog_forms.get(tense_name, {}).get(form_name)
                    ]
                    if analog_forms:
                        print(f"{indent}{'analogs':<{SUBLINE_LABEL_WIDTH}} {', '.join(analog_forms)}")

                if media:
                    spoken = spoken_text(deck, verb.lemma, tense_name, form_name, form)
                    status = "found" if media.find(verb.lemma, spoken) else "missing"
                    print(f"{indent}{'audio':<{SUBLINE_LABEL_WIDTH}} '{spoken}.mp3' [{status}]")

def show_verb(
    deck_name: str,
    lemma: str,
    tense: str | None,
    person: str | None,
    output_format: str,
    include_context: bool,
    include_analogs: bool,
    include_audio: bool,
    output: Path | None,
) -> None:
    deck_dir, deck, verbs = load_resolved_verbs(deck_name)
    if lemma not in verbs:
        raise ValueError(f"Unknown verb in {deck_name}: {lemma}")

    selections = select_forms(deck, verbs[lemma], tense, person)
    if output_format in ("text", "plaintext"):
        if output:
            raise ValueError("--output is only available with --format anki")
        media = PronunciationMedia(deck_dir) if include_audio else None
        print_forms(deck, selections, include_context, include_analogs, media)
        return

    if include_context:
        raise ValueError("--include-context has no effect with --format anki; cards always include context")
    if include_analogs:
        raise ValueError("--include-analogs has no effect with --format anki; cards always include analogs")
    if include_audio:
        raise ValueError("--include-audio has no effect with --format anki; cards include every recording found")

    anki = AnkiDeck(deck, {lemma: verbs[lemma]}, deck_dir)
    anki.write(
        output or Path(f"kofiish_{deck_name}_{lemma}.apkg"),
        selections,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="KOFI deck builder"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # list
    subparsers.add_parser(
        "list",
        help="list all decks",
    )

    # build <deck_name>
    build_parser = subparsers.add_parser(
        "build",
        help="build a deck",
    )
    build_parser.add_argument(
        "deck_name",
        help="name of the deck to build",
    )
    build_parser.add_argument(
        "--output",
        type=Path,
        help="path for the generated Anki package",
    )

    # show <deck_name> <lemma>
    show_parser = subparsers.add_parser(
        "show",
        help="print or export a verb's conjugated forms",
    )
    show_parser.add_argument("deck_name", help="name of the deck")
    show_parser.add_argument("lemma", help="verb infinitive")
    show_parser.add_argument("--tense", help="limit output to one tense")
    show_parser.add_argument("--person", help="limit output to one person, such as 1sg")
    show_parser.add_argument(
        "--format",
        choices=("plaintext", "text", "anki"),
        default="plaintext",
        help="output as plaintext (default) or an Anki package",
    )
    show_parser.add_argument(
        "--include-context",
        action="store_true",
        help="add an extra line with each form's cue and hint",
    )
    show_parser.add_argument(
        "--include-analogs",
        action="store_true",
        help="add an extra line with each form's analog verb forms",
    )
    show_parser.add_argument(
        "--include-audio",
        action="store_true",
        help="add an extra line with each form's expected recording and whether it was found",
    )
    show_parser.add_argument(
        "--output",
        type=Path,
        help="path for an Anki package; defaults to kofiish_<deck>_<verb>.apkg",
    )

    args = parser.parse_args()

    try:
        if args.command == "list":
            list_decks()
        elif args.command == "build":
            build_deck(args.deck_name, args.output)
        elif args.command == "show":
            show_verb(
                args.deck_name,
                args.lemma,
                args.tense,
                args.person,
                args.format,
                args.include_context,
                args.include_analogs,
                args.include_audio,
                args.output,
            )
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
