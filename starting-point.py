from hashlib import sha1
import hmac
from base64 import b64encode
import binascii
from urllib import quote, quote_plus
from time import time
from random import choice
import requests
import json
from os import getenv, remove
import pprint
import csv


OAUTH_CONSUMER_KEY = getenv('OAUTH_CONSUMER_KEY')
OAUTH_CONSUMER_SECRET = getenv('OAUTH_CONSUMER_SECRET')
OAUTH_ACCESS_TOKEN = getenv('OAUTH_ACCESS_TOKEN')
OAUTH_ACCESS_TOKEN_SECRET = getenv('OAUTH_ACCESS_TOKEN_SECRET')

RAND_CHOICE_SET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


def generate_signature(header, method, url, update_header={}):
    for key, value in update_header.items():
        header[key] = value
    # header['include_entities'] = True

    key = "{}&{}".format(OAUTH_CONSUMER_SECRET, OAUTH_ACCESS_TOKEN_SECRET)
    raw = "{}&{}&{}".format(
        method,
        quote_plus(url),
        quote(
            "&".join(
                '{}={}'.format(quote(key), quote(str(value))) for key, value in sorted(header.items())
                )
            )
        )

    print raw

    hashed = hmac.new(key, raw, sha1)
    return binascii.b2a_base64(hashed.digest())[:-1]

def create_header(method, url, update_header={}):
    header = {
        'oauth_consumer_key': OAUTH_CONSUMER_KEY,
        'oauth_nonce': b64encode(''.join(choice(RAND_CHOICE_SET) for i in range(24))),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time())),
        'oauth_token': OAUTH_ACCESS_TOKEN,
        'oauth_version': '1.0'
    }

    header['oauth_signature'] = generate_signature(header.copy(), method, url, update_header)

    return "OAuth {}".format(", ".join('{}="{}"'.format(quote(key), quote(str(value))) for key, value in sorted(header.items())))

def post_tweet(tweet):
    url = "https://api.twitter.com/1.1/statuses/update.json"
    payload = {'status': tweet}
    oauth_string = "{}".format(create_header('POST', url, payload))
    response = requests.post(url, data=payload, headers={'Authorization': oauth_string})

    if (response.status_code==requests.codes.ok):
        return response.text
    else:
        print "response.status_code ", response.status_code
        print "response.reason ", response.reason
        return oauth_string

def search(query):
    url = "https://api.twitter.com/1.1/search/tweets.json"
    payload = {'q': query}
    oauth_string = "{}".format(create_header('GET', url, payload))
    response = requests.get(url, params=payload, headers={'Authorization': oauth_string})

    if (response.status_code==requests.codes.ok):
        return response.text
    else:
        print "response.status_code ", response.status_code
        print "response.reason ", response.reason
        return oauth_string

def user_tweets(screen_name):
    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
    payload = {'screen_name': screen_name, 'count': 200}

    oauth_string = "{}".format(create_header('GET', url, payload))
    response = requests.get(url, params=payload, headers={'Authorization': oauth_string})

    try:
        remove('tweets.csv')
    except OSError:
        pass
    while (response.status_code==requests.codes.ok):
        with open('tweets.csv', 'ab') as f:
            writer = csv.writer(f)
            statuses = json.loads(response.text)
            status_ids = []
            for status in statuses:
                print [status['id'], status['text'].encode('utf-8'), status['created_at']]
                writer.writerow([status['id'], status['text'].encode('utf-8'), status['created_at']])

                status_ids.append(status['id'])

        if not status_ids:
            break

        max_id = sorted(status_ids)[0]

        payload['max_id'] = max_id - 1
        oauth_string = "{}".format(create_header('GET', url, payload))
        response = requests.get(url, params=payload, headers={'Authorization': oauth_string})
    else:
        print "response.status_code ", response.status_code
        print "response.reason ", response.reason
        return oauth_string
    return 'CSV created'

print(user_tweets("TweetsFromAaron"))


# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(json.loads(search('@tweetsfromaaron')))
# pp.pprint(post_tweet("Blah blah blah"))
# pp.pprint(json.loads(response_str))
