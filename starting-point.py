from hashlib import sha1
import hmac
import base64
import urllib
import time
import random
import requests
import json
import os


OAUTH_CONSUMER_KEY = os.getenv('OAUTH_CONSUMER_KEY')
OAUTH_CONSUMER_SECRET = os.getenv('OAUTH_CONSUMER_SECRET')
OAUTH_ACCESS_TOKEN = os.getenv('OAUTH_ACCESS_TOKEN')
OAUTH_ACCESS_TOKEN_SECRET = os.getenv('OAUTH_ACCESS_TOKEN_SECRET')

RAND_CHOICE_SET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


def get_seconds_since_epoch():
    now = datetime.datetime.now()
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = now - epoch
    return int(delta.total_seconds())

def generate_signature(header, tweet, method, url):
    header['status'] = tweet
    # header['include_entities'] = True

    key = "{}&{}".format(OAUTH_CONSUMER_SECRET, OAUTH_ACCESS_TOKEN_SECRET)
    raw = "{}&{}&{}".format(
        method,
        urllib.quote_plus(url),
        urllib.quote(
            "&".join(
                '{}={}'.format(urllib.quote(key), urllib.quote(str(value))) for key, value in sorted(header.items())
                )
            )
        )

    hashed = hmac.new(key, raw, sha1)
    return base64.b64encode(hashed.digest()).rstrip('\n')

def create_header(tweet, method, url):
    header = {
        'oauth_consumer_key': OAUTH_CONSUMER_KEY,
        'oauth_nonce': base64.b64encode(''.join(random.choice(RAND_CHOICE_SET) for i in range(24))),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_token': OAUTH_ACCESS_TOKEN,
        'oauth_version': '1.0'
    }

    header['oauth_signature'] = generate_signature(header.copy(), tweet, method, url)

    return "OAuth {}".format(", ".join('{}="{}"'.format(urllib.quote(key), urllib.quote(str(value))) for key, value in header.items()))

def post_tweet(tweet):
    url = "https://api.twitter.com/1.1/statuses/update.json"
    payload = {'status': tweet}
    oauth_string = "{}".format(create_header(tweet, 'POST', url))

    response = requests.post(url, data=payload, headers={'Authorization': oauth_string})

    if (response.status_code==requests.codes.ok):
        return response.text
    else:
        print "response.status_code ", response.status_code
        print "response.reason ", response.reason

    return oauth_string


print post_tweet("This is a tweet from my python twitter api")
