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
import argparse
import sys


USER_TWEETS_OUTPUT_FILE = 'dump_tweets.csv'

OAUTH_CONSUMER_KEY = getenv('OAUTH_CONSUMER_KEY')
OAUTH_CONSUMER_SECRET = getenv('OAUTH_CONSUMER_SECRET')
OAUTH_ACCESS_TOKEN = getenv('OAUTH_ACCESS_TOKEN')
OAUTH_ACCESS_TOKEN_SECRET = getenv('OAUTH_ACCESS_TOKEN_SECRET')

RAND_CHOICE_SET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def generate_signature(header, method, url, update_header={}):
    for key, value in update_header.items():
        header[key] = value
    # header['include_entities'] = True

    key = "{}&{}".format(OAUTH_CONSUMER_SECRET, OAUTH_ACCESS_TOKEN_SECRET)
    raw = "{}&{}&{}".format(
        method,
        quote_plus(str(url)),
        # quote(
        #     "&".join(
        #          '{}={}'.format(quote(key), quote(str(value))) for key, value in sorted(header.items())
        #         )
        #     )
        quote(
                "&".join([str(k)+"="+quote(str(header[k]), "-._~") for k in sorted(header)]), "-._~"
            )
        )

    print "raw ", raw

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

def statuses_destroy():
    url = "https://api.twitter.com/1.1/statuses/destroy/{}.json"
    try:
        with open('destroy_tweets.csv', 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                del_url = url.format(row[0])

                oauth_string = "{}".format(create_header('POST', del_url))
                print "oauth_string ", oauth_string
                print "del_url '{}''".format(del_url)

                response = requests.post(url, data=None, headers={'Authorization': oauth_string})
                if (response.status_code != requests.codes.ok):
                    sys.stderr.write("response.status_code {}\n".format(response.status_code))
                    sys.stderr.write("response.reason {}\n".format(response.reason))
    except IOError as e:
        sys.stderr("I/O error({0}): {1}".format(e.errno, e.strerror))

    return 'CSV created'

def post_tweet(tweet):
    url = "https://api.twitter.com/1.1/statuses/update.json"
    payload = {'status': tweet}
    oauth_string = "{}".format(create_header('POST', url, payload))

    print "tweet ", tweet

    response = requests.post(url, data=payload, headers={'Authorization': oauth_string})

    if (response.status_code==requests.codes.ok):
        return response.text
    else:
        sys.stderr.write("response.status_code {}\n".format(response.status_code))
        sys.stderr.write("response.reason {}\n".format(response.reason))
        return oauth_string

def search(query):
    url = "https://api.twitter.com/1.1/search/tweets.json"
    payload = {'q': query}
    oauth_string = "{}".format(create_header('GET', url, payload))
    response = requests.get(url, params=payload, headers={'Authorization': oauth_string})

    if (response.status_code==requests.codes.ok):
        return json.loads(response.text)
    else:
        sys.stderr.write("response.status_code {}\n".format(response.status_code))
        sys.stderr.write("response.reason {}\n".format(response.reason))
        return oauth_string

def user_tweets(screen_name):
    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
    payload = {'screen_name': screen_name, 'count': 200}

    oauth_string = "{}".format(create_header('GET', url, payload))
    response = requests.get(url, params=payload, headers={'Authorization': oauth_string})

    try:
        remove(USER_TWEETS_OUTPUT_FILE)
    except OSError:
        pass
    while (response.status_code==requests.codes.ok):
        with open(USER_TWEETS_OUTPUT_FILE, 'ab') as f:
            writer = csv.writer(f)
            statuses = json.loads(response.text)
            status_ids = []
            for status in statuses:
                sys.stdout.write("\t".join([str(status['id']), status['text'], status['created_at']]))
                sys.stdout.write("\n")
                writer.writerow([str(status['id']), "", status['text'].encode('utf-8'), status['created_at']])

                status_ids.append(status['id'])

        if not status_ids:
            break

        max_id = sorted(status_ids)[0]

        payload['max_id'] = max_id - 1
        oauth_string = "{}".format(create_header('GET', url, payload))
        response = requests.get(url, params=payload, headers={'Authorization': oauth_string})
    else:
        sys.stderr.write("response.status_code {}\n".format(response.status_code))
        sys.stderr.write("response.reason {}\n".format(response.reason))
        return oauth_string
    return True


functions = {
    "search": search,
    "post_tweet": post_tweet,
    "statuses_destroy": statuses_destroy,
    "user_tweets": user_tweets
}

parser = argparse.ArgumentParser(description='Tweet-of-nut')
parser.add_argument(
    'function',
    metavar='function',
    type=str,
    nargs=1,
    choices=functions.keys(),
    help='The function to run'
)

parser.add_argument(
    'function_args',
    metavar='function_args',
    type=str,
    nargs='*',
    help='Args for the function'
)

args = parser.parse_args()

if (args.function[0] in ['search']):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(functions[args.function[0]](*args.function_args))
elif (args.function[0] in ['post_tweet']):
    functions[args.function[0]](' '.join(args.function_args))
else:
    functions[args.function[0]](*args.function_args)
