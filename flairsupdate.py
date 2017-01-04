import praw
import flairdb
from configparser import ConfigParser

conf = ConfigParser()
conf.read('config.ini')
client_id = conf.get('script', 'client_id')
client_secret = conf.get('script', 'client_secret')
username = conf.get('account', 'username')
password = conf.get('account', 'password')
user_agent = conf.get('api', 'user_agent')
subreddit = conf.get('subreddit', 'name')
flairmode = int(conf.get('script', 'flairsmode'))

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     username=username,
                     password=password,
                     user_agent=user_agent)
subreddit = reddit.subreddit(subreddit)

ranks = {
    0: 'bronze',
    1500: 'silver',
    2000: 'gold',
    2500: 'platinum',
    3000: 'diamond',
    3500: 'master',
    5000: 'grandmaster'
}


def update_user_flair(user):
    lastrank = int(user.last_rank)
    toprank = int(user.top_rank)
    lastflair = ''
    topflair = ''
    flairimage = ''
    for startrank in sorted(ranks.iteritems()):
        if lastrank >= startrank[0]:
            lastflair = startrank[1]
        if toprank >= startrank[0]:
            topflair = startrank[1]

    if flairmode == 0:
        if topflair == 'master' or topflair == 'grandmaster':
            if lastflair == 'master' or lastflair == 'grandmaster':
                flairimage = lastflair
            else:
                flairimage = 'diamond'
        else:
            flairimage = topflair
    elif flairmode == 1:
        flairimage = lastflair
    else:
        flairimage = topflair
    subreddit.flair.set(user.reddit_username, str(lastrank) +
                        " (High: " + str(toprank) + ")", "rank " + flairimage)


def update_all():
    users = flairdb.get_all_users()
    for user in users:
        update_user_flair(user)


def main():
    update_all()

if __name__ == "__main__":
    main()
