import json

from flask import Flask, render_template
import requests
from secrets import token

app = Flask(__name__)


def get_new_pushes(last_id):
    to_return = []
    all_events = json.loads(requests.get('https://api.github.com/events?access_token='+token).content)
    new_last_id = all_events[0]['id']
    for event in all_events:
        if int(event['id']) <= last_id:
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
    full_list = get_messages(get_commits(get_new_pushes(0)))
    return render_template("index.html", list=full_list)


if __name__ == '__main__':
    app.run(debug=True)
