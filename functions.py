import sys
import json
import requests
import pandas as pd


def get_token():
    with open("config.json", "r") as f:
        config = json.load(f)
    CLIENT_KEY = config["CLIENT_KEY"]
    CLIENT_SECRET = config["CLIENT_SECRET"]
    url = "https://api.tcgplayer.com/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_KEY,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=body)
    if response.status_code != 200:
        print("Error getting bearer token.")
    else:
        print("Retrieved token from TCGPlayer API.")
        return response.json()["access_token"]


def download_sets(token, categories):
    sets = {
        "Pokemon": {},
        "YuGiOh": {},
        "Flesh & Blood": {},
    }
    for category in categories.keys():
        url = "https://api.tcgplayer.com/catalog/groups"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "categoryId": categories[category],
            "isSupplemental": False,
            "sortOrder": "groupId",
            "sortDesc": True,
            "limit": 25,
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error downloading sets for {category}.")
            sys.exit()
        else:
            data = response.json()["results"]
            for s in data:
                sets[category][s["name"]] = s["groupId"]

    codes = {}
    for category in sets.keys():
        codes[category] = []
        for code in sets[category].items():
            codes[category].append(f"{code[1]} - {code[0]}")

    return sets, codes


def download_cards(token, group):
    cards = []
    offset = 0
    pending = True
    while pending:
        url = "https://api.tcgplayer.com/catalog/products"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "groupId": group["code"],
            "getExtendedFields": True,
            "productTypes": "cards",
            "limit": 500,
            "offset": offset,
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200 and response.json()["success"] != True:
            print("Error getting products.")
            sys.exit()
        else:
            data = response.json()["results"]
            cards = cards + data
        if len(data) == 100:
            offset += 100
        else:
            pending = False
    return cards


def get_prices(token, cards):
    list_of_cards = [str(card["productId"]) for card in cards]
    prices = {}
    offset = 0
    pending = True
    while pending:
        sliced = list_of_cards[offset:offset+100]
        card_ids = ",".join(sliced)
        url = "https://api.tcgplayer.com/pricing/product/productIds"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "productIds": card_ids
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("Error getting prices.")
            sys.exit()
        data = response.json()["results"]
        for p in data:
            variant = p["subTypeName"]
            pid = p["productId"]
            lp = p["lowPrice"] if p["lowPrice"] is not None else 0
            mp = p["marketPrice"] if p["marketPrice"] is not None else 0
            if pid in prices:
                prices[pid][variant] = mp if mp > lp else lp
            else:
                prices[pid] = {}
                prices[pid][variant] = mp if mp > lp else lp
        if len(sliced) == 100:
            offset += 100
        else:
            pending = False
    return prices


def format_cards(token, cards, group):
    category = group["category"]
    set_name = group["set_name"]
    prices = get_prices(token, cards)
    variant_types = {
        "Pokemon": {
            "Holofoil": "H",
            "Reverse Holofoil": "RH",
            "Normal": "N",
            "1st Edition Normal": "1N",
            "1st Edition Holofoil": "1H",
        },
        "YuGiOh": {
            "Unlimited": "U",
            "1st Edition": "1E",
            "Limited": "L",
        },
        "Flesh & Blood": {
            "1st Edition Normal": "1N",
            "1st Edition Cold Foil": "1CF",
            "1st Edition Rainbow Foil": "1RF",
            "Unlimited Edition Normal": "UN",
            "Unlimited Edition Rainbow Foil": "URF"
        },
    }
    formatted_variants = []
    for card in cards:
        pid = card["productId"]
        card_handle = card["cleanName"].replace(" ", "-").lower()
        card_title = card["cleanName"]
        card_image = card["imageUrl"]
        ed = {"Description": "", }
        for data in card["extendedData"]:
            if data["name"] == "Number":
                ed[data["name"]] = data["value"].replace(" // ", " ")
            elif data["name"] in ["CardType", "Class"]:
                ed[data["name"]] = data["value"].replace(";", " ")
            else:
                ed[data["name"]] = data["value"]
        tags_list = []
        for key in ed.keys():
            if key in ["CardType", "Class", "Rarity", "Number"]:
                tags_list.append(ed[key])
        tags = " ".join(tags_list)
        for v in variant_types[category].keys():
            formatted_variant = {
                "handle": card_handle,
                "title": card_title,
                "body": ed["Description"],
                "tags": tags + " " + set_name,
                "option1 name": "Title",
                "option1 value": v,
                "variant sku": f"{card_handle}-{variant_types[category][v]}",
                "variant grams": 0,
                "variant inventory tracker": "shopify",
                "variant inventory policy": "deny",
                "variant fulfillment service": "manual",
                "variant price": prices[pid][v],
                "variant requires shipping": "TRUE",
                "variant taxable": "TRUE",
                "image src": card_image,
            }
            formatted_variants.append(formatted_variant)
    return formatted_variants


def cards_to_csv(variants, category_name, file):
    df = pd.DataFrame(variants)
    df["vendor"] = category_name
    df["type"] = "Singles"
    csv = df.to_csv(file, index=False)
    print("CSV saved to current directory!")
