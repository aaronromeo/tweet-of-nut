import tweepy
from os import getenv, remove
import csv
import sys
import argparse


TWITTER_USER = 'tweetsfromaaron'
USER_TWEETS_OUTPUT_FILE = 'dump_tweets.csv'


auth = tweepy.OAuthHandler(getenv('OAUTH_CONSUMER_KEY'), getenv('OAUTH_CONSUMER_SECRET'))
auth.set_access_token(getenv('OAUTH_ACCESS_TOKEN'), getenv('OAUTH_ACCESS_TOKEN_SECRET'))

api = tweepy.API(auth)


def user_tweets(screen_name):
    try:
        remove(USER_TWEETS_OUTPUT_FILE)
    except OSError:
        pass

    try:
        tweets = api.user_timeline(screen_name)
    except tweepy.error.TweepError as e:
        sys.stderr.write("Err: {}\n".format(e))
        return

    while (tweets):
        with open(USER_TWEETS_OUTPUT_FILE, 'ab') as f:
            writer = csv.writer(f)
            status_ids = []
            for status in tweets:
                sys.stdout.write("\t".join([str(status.id), status.text, status.created_at.isoformat()]))
                sys.stdout.write("\n")
                writer.writerow([str(status.id), "", status.text.encode('utf-8'), status.created_at.isoformat()])

                status_ids.append(status.id)

        if not status_ids:
            break

        max_id = sorted(status_ids)[0]

        try:
            tweets = api.user_timeline(TWITTER_USER, max_id=max_id-1)
            # for tweet in tweets:
            #     print tweet.text
        except tweepy.error.TweepError as e:
            sys.stderr.write("Err: {}\n".format(e))
            break

    return True

def statuses_destroy():
    try:
        with open('destroy_tweets.csv', 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    status = api.destroy_status(row[0])
                except tweepy.error.TweepError as e:
                    sys.stderr.write("Err: {} {}\n".format(row[0], e))

    except IOError as e:
        sys.stderr("I/O error({0}): {1}".format(e.errno, e.strerror))


functions = {
    # "search": search,
    # "post_tweet": post_tweet,
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
