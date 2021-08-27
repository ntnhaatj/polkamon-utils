import argparse
from termcolor import colored

from utils import get_metadata
from datatypes import Metadata


def main(args: list):
    metadata = get_metadata(args.id)
    meta = Metadata.from_metadata(metadata)
    print(colored(f"Rarity score: {meta.rarity_score}", "green"))
    print(colored(f"Birthday: {meta.attributes.birthday}", "yellow"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)

    args = parser.parse_args()
    main(args)
