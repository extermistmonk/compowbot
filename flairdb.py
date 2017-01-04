from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from configparser import ConfigParser

import ranks
import flairsupdate

conf = ConfigParser()
conf.read('config.ini')
dbname = conf.get('database', 'name')

db = SqliteExtDatabase(dbname)
db.connect()


class User(Model):
    reddit_username = CharField(unique=True)
    bnet_battletag = CharField(unique=True)
    bnet_region = IntegerField()
    last_rank = IntegerField()
    top_rank = IntegerField()

    class Meta:
        database = db  # This model uses the "people.db" database.

db.create_tables([User], safe=True)


def add_user(reddit, battletag, region):
    try:
        User.create(reddit_username=reddit,
                    bnet_battletag=battletag,
                    bnet_region=region, last_rank=0, top_rank=0)
    except IntegrityError:
        return False
    user = User.get(User.reddit_username == reddit)
    ranks.update_user_rank(user)
    flairsupdate.update_user_flair(user)
    return user


def reregister_user(reddit, battletag, region):
    try:
        oldreddit = User.get(User.reddit_username == reddit)
        oldreddit.delete_instance()
    except Exception:
        pass
    add_user(reddit, battletag, region)


def get_all_users():
    return User.select()
