import argparse
from termcolor import colored

from utils import get_metadata
from datatypes import Rarity, Attribute


def get_score(rarity: Rarity) -> int:
    return int(1 / rarity.value / 40)


def main(args: list):
    metadata = get_metadata(args.id)
    rarity = Rarity.from_metadata(metadata)
    attribute = Attribute.from_metadata(metadata)
    print(colored(f"Rarity score: {get_score(rarity)}", "green"))
    print(colored(f"Birthday: {attribute.birthday}", "yellow"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)

    args = parser.parse_args()
    main(args)
