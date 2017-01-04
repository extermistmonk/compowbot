import requests
import requests.auth
import os
from configparser import ConfigParser
import praw

import regions
import flairdb
import ranks
import flairsupdate

from datetime import timedelta
from flask import Flask, abort, request, session, redirect, url_for
from OpenSSL import SSL
from uuid import uuid4

conf = ConfigParser()
conf.read('config.ini')
reddit_client_id = conf.get('api', 'reddit_client_id')
reddit_client_secret = conf.get('api', 'reddit_client_secret')
user_agent = conf.get('api', 'user_agent')
bnet_client_id = conf.get('api', 'bnet_client_id')
bnet_client_secret = conf.get('api', 'bnet_client_secret')
home_uri = conf.get('web', 'home_uri')
port = int(conf.get('web', 'port'))
ssl_cert = conf.get('ssl', 'cert')
ssl_key = conf.get('ssl', 'key')

BNET_REDIRECT_URI = home_uri + "bnet_callback"
REDDIT_REDIRECT_URI = home_uri + "reddit_callback"

reddit = praw.Reddit(user_agent=user_agent,
                     client_id=reddit_client_id,
                     client_secret=reddit_client_secret,
                     redirect_uri=REDDIT_REDIRECT_URI)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=5)


@app.route('/')
def homepage():
    session.permanent = True
    state = str(uuid4())
    session['state'] = state

    text = ""

    if request.args.has_key('region'):
        region = int(request.args.get('region'))
        if region >= 0 and region <= len(regions.regions):
            session['region'] = region
            return redirect(reddit.auth.url(['identity'], state, 'temporary'))
        else:
            text += "Invalid region<br>"

    text += 'Select your Battle.net region<br><form name="region" action="?" method="GET"><select name="region">'
    for value in regions.regions:
        text += '<option value=' + str(value) + '>' + \
                regions.regions[value] + '</option>'
    text += '<input type="submit" value="Next"></select></form>'
    return text


@app.route('/reddit_callback')
def reddit_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    code = request.args.get('code')
    reddit.auth.authorize(code)
    region = int(session['region'])
    if session.has_key('region') and region >= 0 and region <= len(regions.regions):
        return redirect(make_bnet_authorization_url(region))
    else:
        return "Invalid region saved in session. Restart your browser and try again."


@app.route('/bnet_callback')
def bnet_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    code = request.args.get('code')
    session['bnetcode'] = code
    session['bnettoken'] = get_bnet_token(session['bnetcode'])
    return redirect(url_for('submit'))


@app.route('/submit')
def submit():
    redditname = reddit.user.me().name
    bnetname = get_bnet_username(session['bnettoken'])

    region = int(session['region'])
    if region < 0 or region > len(regions.regions):
        return "Invalid region saved in session. Restart your browser and try again."

    if request.args.has_key('action'):
        if request.args['action'] == 'reregister':
            flairdb.reregister_user(redditname, bnetname, region)
            return "Accounts re-registered"

    user = flairdb.add_user(redditname, bnetname, region)
    if user == False:
        return "Reddit or Battle.net account is/are already registered, would you like to re-register your reddit account?" + '<br><form action="/submit" method="get"><button type="submit" name="action" value="reregister" id="reregister">Re-register Reddit Account</button></form>'
    ranks.update_user_rank(user)
    flairsupdate.update_user_flair(user)
    return "Accounts registered"


def make_bnet_authorization_url(region):
    state = session['state']
    regionstr = regions.regions[region]
    params = {"client_id": bnet_client_id,
              "response_type": "code",
              "state": state,
              "redirect_uri": BNET_REDIRECT_URI,
              "duration": "temporary",
              "scope": "sc2.profile"}
    import urllib
    url = "https://" + regionstr + \
        ".battle.net/oauth/authorize?" + urllib.urlencode(params)
    return url


def get_bnet_token(code):
    client_auth = requests.auth.HTTPBasicAuth(
        bnet_client_id, bnet_client_secret)
    post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": BNET_REDIRECT_URI,
                 "scope": "sc2.profile"}
    response = requests.post("https://us.battle.net/oauth/token",
                             auth=client_auth,
                             data=post_data)
    token_json = response.json()
    return token_json["access_token"]


def get_bnet_username(access_token):
    post_data = {"access_token": access_token}
    response = requests.get(
        "https://us.api.battle.net/account/user?", params=post_data)
    me_json = response.json()
    return me_json['battletag']
    import urllib
    return "https://us.api.battle.net/account/user?" + urllib.urlencode(post_data)

if __name__ == '__main__':
    context = (ssl_cert, ssl_key)
    app.run(debug=True, port=port, ssl_context=context)
