import json
import requests
import re
import threading
import tweepy as tweepy
from time import sleep
from secrets import github_token, twitter_keys


profanity = ['\barse\b', 'bastard', 'bitch', 'bloody', 
             'bollocks', '\bcock', '\bcunt\b', '\bdamn\b', 
             '\bdick\b', '\bfml\b', 'fuck', '\bnaff\b', 
             '\bpiss', '\bpoo\b', '\bshit', 'shit\b', '\btits\b', 
             '\btosser\b', '\btwat', '\bwank', '\bwhore', 
             '\bwtf\b', '\btifu\b']

new_last_id = int(0)

keep_going = True


def get_new_pushes(last_id):
    global new_last_id
    to_return = []
    try:
        all_events = json.loads(requests.get(
            'https://api.github.com/events?access_token=' 
            + github_token).content)
        
        for event in all_events:
            if int(event['id']) <= int(last_id):
                return to_return
            if event['type'] == 'PushEvent':
                to_return.append(event)
    # if kicked by GitHub, wait a bit so we're not causing them a spot of bother
    except requests.ConnectionError:
        sleep(30)
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
    # get all the messags since we last checked
    messages = add_messages()
    for message in messages:
        # If there is profanity in this commit message
        if re.match(r".*(" + '|'.join(profanity) + ").*", message, re.IGNORECASE):
            # If this isn't a merge, as a number of users/repos 
            # get matched by the profanity checker which is a bit boring
            if not re.match(r"^Merge", message, re.IGNORECASE):
                tweet(re.sub("@","",message)) # Remove handles to prevent abuse


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
    try:
        api.update_status(status=message)
    except tweepy.TweepError:
        # if the same commit message is used twice in a row, only send it once
        pass


def keep_tweeting():
    tweet_new_messages()
    # TODO: maybe put in the ability to stop it tweeting
    if keep_going:
        threading.Timer(1, keep_tweeting).start()

keep_tweeting()
