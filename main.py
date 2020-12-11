from __future__ import print_function, unicode_literals
import sys
from PyInquirer import prompt
import pyfiglet

from functions import get_token, download_sets, download_cards, format_cards, cards_to_csv


def main():

    categories = {
        "Pokemon": 3,
        "YuGiOh": 2,
        "Flesh & Blood": 62,
    }

    logo = pyfiglet.figlet_format("tcgify", font="slant")
    print(logo)
    print("Welcome to TCGify!\n")
    print("Retrieving new token...")
    token = get_token()
    print("Updating set list...")
    sets, codes = download_sets(token, categories)

    questions = [
        {
            "type": "list",
            "name": "category",
            "message": "What category are you interested in?",
            "choices": ["Pokemon", "YuGiOh", "Flesh & Blood"]
        },
        {
            "type": "list",
            "name": "Pokemon",
            "message": "Which Pokemon set do you want to download?",
            "choices": codes["Pokemon"],
            "when": lambda answers: answers["category"] == "Pokemon"
        },
        {
            "type": "list",
            "name": "YuGiOh",
            "message": "Which YuGiOh set do you want to download?",
            "choices": codes["YuGiOh"],
            "when": lambda answers: answers["category"] == "YuGiOh"
        },
        {
            "type": "list",
            "name": "Flesh & Blood",
            "message": "Which Flesh & Blood set do you want to download?",
            "choices": codes["Flesh & Blood"],
            "when": lambda answers: answers["category"] == "Flesh & Blood"
        },
        {
            "type": "list",
            "name": "confirm",
            "message": "Is the information above correct?",
            "choices": ["Yes", "No"]
        },
    ]

    answers = prompt(questions)

    if answers["confirm"] == "No":
        print("Exiting...goodbye!")
        sys.exit()

    group = {
        "category": answers["category"],
        "set_name": answers[answers["category"]].split(" - ")[1],
        "code": answers[answers["category"]].split(" - ")[0],
    }

    print(f"Downloading cards for {group['set_name']}...")
    cards = download_cards(token, group)
    print(f"Found {len(cards)} cards.")

    print("Building variants...")
    variants = format_cards(token, cards, group)

    filename = f"{group['code']}_{group['set_name'].replace(' ', '_')}.csv"
    df = cards_to_csv(variants, group["category"], filename)
