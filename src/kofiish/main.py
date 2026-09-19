import argparse
from pathlib import Path

from kofiish.anki import AnkiDeck
from kofiish.deck import DeckLoader


DECKS_DIR = Path("decks")


def list_decks() -> None:
    print("Available decks:")
    for path in sorted(DECKS_DIR.iterdir()):
        if path.is_dir() and (path / "deck.yaml").exists():
            print("\t- " + path.name)


def build_deck(deck_name: str) -> None:
    deck_dir = DECKS_DIR / deck_name
    deck_path = deck_dir / "deck.yaml"

    if not deck_path.exists():
        print(f"Unknown deck: {deck_path}")
        return

    deck = DeckLoader().load(deck_path)
    deck.load_verbs(deck_dir / "verbs")

    anki = AnkiDeck(deck, deck_dir)

    anki.write("kofi_" + deck_name + ".apkg")


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

    args = parser.parse_args()

    if args.command == "list":
        list_decks()
    elif args.command == "build":
        build_deck(args.deck_name)


if __name__ == "__main__":
    main()
