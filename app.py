import json

from flask import Flask, render_template
import requests
import threading
import tweepy as tweepy
from secrets import github_token, twitter_keys

app = Flask(__name__)

new_last_id = int(0)
all_commits = []
keep_filling = True


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


@app.route('/')
def root():
    global all_commits
    return render_template("index.html", list=all_commits)


def add_messages(list_so_far):
    global new_last_id
    full_list = get_messages(get_commits(get_new_pushes(new_last_id))) + list_so_far
    return full_list


def fill_list():
    global all_commits, keep_filling
    all_commits = add_messages(all_commits)
    if keep_filling:
        threading.Timer(1, fill_list).start()


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
    api.update_status(status = message + " #LocalHackDay")

fill_list()

if __name__ == '__main__':
    app.run(debug=True)
