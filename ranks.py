import urllib
import requests

import flairdb
import regions


def update_user_rank(user):
    rank = get_rank(user)
    if rank > user.last_rank:
        user.top_rank = rank
    user.last_rank = rank
    user.save()


def update_all():
    users = flairdb.get_all_users()
    for user in users:
        update_user_rank(user)


def get_rank(user):
    battletag = user.bnet_battletag
    region = user.bnet_region
    response = requests.get(
        "https://api.lootbox.eu/pc/" + regions.regions[region] + "/" + battletag.replace('#', '-') + "/profile")
    token_json = response.json()
    return int(token_json['data']['competitive']['rank'])


def main():
    update_all()

if __name__ == "__main__":
    main()
