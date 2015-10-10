import json
import requests
import re
import threading
import tweepy as tweepy
from secrets import github_token, twitter_keys

profanity = [' arse ', 'bastard', 'bitch', 'bloody', 'bollocks', ' cock', 'cunt', 'damn', 'dick', 'fuck', 'naff', 'piss', 'shit', 'tits', 'tosser', 'twat', 'wank', 'whore', 'wtf']
new_last_id = int(0)

keep_going = True


def get_new_pushes(last_id):
    global new_last_id
    to_return = []
    all_events = json.loads(requests.get('https://api.github.com/events?access_token=' + github_token).content)
    new_last_id = all_events[0]['id']
    for event in all_events:
        if int(event['id']) <= int(last_id):
            return to_return
        if event['type'] == 'PushEvent':
            to_return.append(event)
    return to_return


def get_commits(push_events):
    to_return = []
    for event in push_events:
        commits = event['payload']['commits']
        for commit in commits:
            to_return.append(commit)
    return to_return


def get_messages(commits):
    to_return = []
    for commit in commits:
        message = commit['message']
        if message.find('\n\n') >= 0:
            message = message[:message.find('\n\n')]  # only get the first line of the message
        to_return.append(message)
    return to_return


def add_messages():
    global new_last_id
    full_list = get_messages(get_commits(get_new_pushes(new_last_id)))
    return full_list


def tweet_new_messages():
    messages = add_messages()
    for message in messages:
        if re.match(r".*(" + '|'.join(profanity) + ").*", message, re.IGNORECASE):
            tweet(message)


def tweet(message):
    CONSUMER_KEY = twitter_keys['consumer_key']
    CONSUMER_SECRET = twitter_keys['consumer_secret']
    ACCESS_TOKEN = twitter_keys['access_token']
    ACCESS_TOKEN_SECRET = twitter_keys['access_token_secret']

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print('Error! Failed to get request token.')

    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    api.update_status(status=message)


def keep_tweeting():
    tweet_new_messages()
    # TODO: maybe put in the ability to stop it tweeting
    if keep_going:
        threading.Timer(1, keep_tweeting).start()
