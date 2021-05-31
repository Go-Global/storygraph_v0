# Takes in twitter data and parses it into storygraph schema
import datetime

from graph_driver import GraphDBDriver
from soup_models import StoryGraph, Source, Document, Authored, Interacts, References

import requests, os, json

from dotenv import dotenv_values

config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}

class TwitterAPI:
    def __init__(self, config):
        self.config = config
        self.headers = self.create_headers()

    # Specify the usernames that you want to lookup below
    # You can enter up to 100 comma-separated values.
    # returns users
    def query_users(self, user_list, full_data=False):
        assert len(user_list) <= 100, "Too many accounts passed in: " + str(len(user_list))
        usernames = "usernames={}".format(",".join(user_list))
        url = "https://api.twitter.com/2/users/by?{}".format(usernames)
        if full_data:
            params = self.get_user_params("created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld")
        else:
            params = self.get_user_params("id,description,location,name")
        json_response = self.connect_to_endpoint(url, self.headers, params)
        return json_response

    # returns tweets from user
    def get_user_tweet_timeline(self, user_id):
        url = "https://api.twitter.com/2/users/{}/tweets".format(user_id)
        params = self.get_tweet_params("created_at")
        json_response = self.connect_to_endpoint(url, self.headers, params)
        return json_response

    # returns tweets mentioning user
    def get_user_mention_timeline(self, user_id):
        url = "https://api.twitter.com/2/users/{}/mentions".format(user_id)
        params = self.get_tweet_params("created_at")
        json_response = self.connect_to_endpoint(url, self.headers, params)
        return json_response

    # returns users that are followed/following user_id
    def get_following(self, user_id, full_data=False, next_token=None):
        # Replace with user ID below
        # user_id = 2244994945
        url = "https://api.twitter.com/2/users/{}/following".format(user_id)
        headers = self.create_headers()
        if full_data:
            params = self.get_user_params("created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld")
        else:
            params = self.get_user_params("id,description,location,name")
        if next_token:
            params['pagination_token'] = next_token
        json_response = self.connect_to_endpoint(url, headers, params)
        token = None
        if 'meta' in json_response.keys():
            token = json_response['meta']['next_token']
        return json_response, token
    
    # returns users that are followed/following user_id, as well as a pagination token when provided
    def get_followers(self, user_id, full_data=False, next_token=None):
        # Replace with user ID below
        # user_id = 2244994945
        url = "https://api.twitter.com/2/users/{}/followers".format(user_id)
        headers = self.create_headers()
        if full_data:
            params = self.get_user_params("created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld")
        else:
            params = self.get_user_params("id,description,location,name")
        if next_token:
            params['pagination_token'] = next_token
        json_response = self.connect_to_endpoint(url, headers, params)
        token = None
        if 'meta' in json_response.keys():
            token = json_response['meta']['next_token']
        return json_response, token

    def format_json(self, json_obj):
        return json.dumps(json_obj, indent=4, sort_keys=True)

    # Tweet fields are adjustable.
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    def get_tweet_params(self, fields):
        params = {"tweet.fields": fields}
        return params
    
    # User fields are adjustable, options include:
    # created_at, description, entities, id, location, name,
    # pinned_tweet_id, profile_image_url, protected,
    # public_metrics, url, username, verified, and withheld
    def get_user_params(self, fields):
        params = {"user.fields": fields}
        return params

    # Auth
    def create_headers(self):
        headers = {"Authorization": "Bearer {}".format(self.config['BEARER_TOKEN'])}
        return headers

    # Actual Request
    def connect_to_endpoint(self, url, headers, params):
        response = requests.request("GET", url, headers=headers, params=params)
        print(response.status_code)
        if response.status_code != 200:
            raise Exception(
                "Request returned an error: {} {}".format(
                    response.status_code, response.text
                )
            )
        return response.json()

def test_twitter():
    twitter = TwitterAPI(config)
    print(twitter.query_users(["stefanlayanto", "elonmusk","spacex"], full_data=True))
    # print(api.get_follows("34743251"))
    # api = twitter.Api(consumer_key=config['CONSUMER_KEY'],
    #                 consumer_secret=config['CONSUMER_SECRET'],
    #                 access_token_key=config['ACCESS_TOKEN'],
    #                 access_token_secret=config['ACCESS_TOKEN_SECRET'])
    # api

def get_tweets():
    results = {
        "1251304796285370368": {
            "conversation_id_str":"1251304796285370368",
            "created_at":"Sat Apr 18 00:21:26 +0000 2020",
            "display_text_range":"[...]",
            "entities":"{...}",
            "extended_entities":"{...}",
            "favorite_count":9598,
            "full_text":"You built a program. You broke records. You won awards. You still have unfinished business.   You’re ready to move the game forward, and now your name has been called. So, what’s next?  You’ll show us.  #justdoit @sabrina_i20 https://t.co/INHqGI7hkf",
            "id_str":"1251304796285370368",
            "lang":"en",
            "possibly_sensitive_editable":True,
            "quote_count":144,
            "reply_count":46,
            "retweet_count":1878,
            "source":"<a href=\"http://twitter.com/download/iphone\" rel=\"nofollow\">Twitter for iPhone</a>",
            "user_id_str":"415859364",
        }
    }
    return results


def format_users(users):
    source_nodes = []
    for user in users:
        # Source(key, name, source_type, attrs=defaultdict(lambda: set())):

        source = Source(user["id"], user["username"], "twitter-user", attrs=user, date_processed=datetime.datetime.now())
        source_nodes.append(source)
    return source_nodes

def format_tweets(tweets):
    doc_nodes = []
    for tweet_id, tweet in tweets.items():
        # def __init__(self, key, title, doc_type, attrs=defaultdict(lambda: set()), spacy_doc=None, date_processed=None):
        doc = Document(tweet_id, tweet["full_text"], "tweet", attrs=tweet, date_processed=datetime.datetime.now())
        doc_nodes.append(doc)
    return doc_nodes

def get_twitter_nodes():
    tweets = get_tweets()
    return format_tweets(tweets)

# Assumes user exists in database
# ret = add_twitter_following_to_graph(twitter, driver, '1398053704071147521', max_followers=100, create_nodes=False)
def add_twitter_following_to_graph(twitter_api, graph_driver, user_key, max_followers=1000, create_nodes=False):
    assert len(graph_driver.query("MATCH (n:source {key:'"+str(user_key)+"'}) RETURN n")) > 0, "Original User not found in graph"
    edge_count, node_count = 0,0
    next_token = None
    following = []
    for _ in range(max_followers//100):
        next_following, next_token = twitter.get_following(user_key, full_data=True, next_token=next_token)
        following.extend(next_following['data'])
        if not next_token:
            break
    print("Found {} followers".format(len(following)))
    if create_nodes:
        sources = format_users(following)
        ret = graph_driver.upload_nodes(sources)
        node_count += len(ret)
    all_node_keys = set([record['n']['key'] for record in graph_driver.query("MATCH (n:source {source_type:'twitter-user'}) RETURN n")])
    exist_count = 0
    edges = []
    for user in following:
#         print(type(user), user)
        if user['id'] in all_node_keys:
            exist_count += 1
            edges.append(Interacts((user['id'], 'source'), (user['id'], 'source'), 'follows'))
    print("of which {} exist in graph".format(exist_count))
    ret = graph_driver.upload_edges(edges)
    edge_count += len(ret)
    print("Success. Added {} edges and {} nodes for user {}.".format(edge_count, node_count, user_key))
    return ret



if __name__ == '__main__':
    # Pull REI
    # Pull all REI's Followers
    # Pull all REI's Following
    # Add all source nodes and add Edges between them

    # class Source(Node)  __init__(self, key, name, source_type, attrs=defaultdict(lambda: set()))
    # class Document(Node) __init__(self, key, title, doc_type, attrs=defaultdict(lambda: set()), spacy_doc=None, date_processed=None)
    # class AllEdges(Edge) __init__(self, source, dest, timestamp=0)
    print("Getting REI Source Node")
    twitter = TwitterAPI(config)
    rei_json = twitter.query_users(["rei"])['data'][0]
    rei = format_users([rei_json])[0]
    print(rei)
    print("Getting follower_list")
    followers = twitter.get_followers(rei.key, full_data=True)
    print(len(followers))
    print(followers)
    # following = twitter.get_following(rei.key, full_data=True)


    # for user in users:
    #     print(user.keys())
    #     for key, value in user.items():
    #         print("Key:", key)
    #         print("value:", value)

    # print("Testing Twitter Parser...")
    # test_twitter()
    # # Get Tweets
    # tweet_nodes = get_twitter_nodes()

    # # Get Users (check if exists in graph database first)
    # driver = GraphDBDriver()
    # driver.upload_nodes(tweet_nodes)
    # driver.close()

    # Upload new tweets (check if exists in GraphDB) and users
    # tweets = get_tweets()
    # users = get_users()
    # author_ids = set()
    # for tweet_id, tweet in tweets.items():
    #     author_ids.add(tweet["user_id_str"])
    
    # print(users.keys())
    # for author_id in author_ids:
    #     if author_id not in users.keys():
    #         print("couldn't find id", author_id)
    #     else:
    #         print("Found author", users[author_id])

    # testGraph = StoryGraph(title="Twitter Test Graph")
    # node_lookup = dict()
    # node_lookup['elon'] = Source("@elonmusk", "Elon Musk", "twitter_account")
    # node_lookup['spacex'] = Source("@SpaceX", "SpaceX", "twitter_account")
    # node_lookup['elontweet1'] = Document('https://twitter.com/elonmusk/status/1392985728271884288', "As always", "tweet")
    # node_lookup['spacextweet1'] = Document('https://twitter.com/SpaceX/status/1393698783515402241', "Live feed of Starlink mission → http://spacex.com/launches", "tweet")
    # node_lookup['spacextweet2'] = Document('https://twitter.com/SpaceX/status/1392926112540364807', "SpaceX’s fifth high-altitude flight test of Starship from Starbase in Texas", "tweet")
    # testGraph.read_node_dict(node_lookup)
    # edges = set()
    # edges.add(Interacts(node_lookup['elon'], node_lookup['spacex']))
    # edges.add(Authored(node_lookup['elon'], node_lookup['elontweet1']))
    # edges.add(Authored(node_lookup['spacex'], node_lookup['spacextweet1']))
    # edges.add(Authored(node_lookup['spacex'], node_lookup['spacextweet2']))
    # testGraph.read_edge_set(edges)
    # testGraph.visualize()

def get_users():
    users = [
        {
            "created_at": "2008-10-03T20:44:36.000Z",
            "description": "A member-owned co-op since 1938.\nShare your adventures with #OptOutside",
            "entities": {
                "description": {
                    "hashtags": [
                        {
                            "end": 71,
                            "start": 60,
                            "tag": "OptOutside"
                        }
                    ]
                },
                "url": {
                    "urls": [
                        {
                            "display_url": "REI.com",
                            "end": 22,
                            "expanded_url": "http://www.REI.com",
                            "start": 0,
                            "url": "http://t.co/Z4sBQwWTQT"
                        }
                    ]
                }
            },
            "id": "16583846",
            "location": "Seattle, WA",
            "name": "REI",
            "pinned_tweet_id": "1395741169263554567",
            "profile_image_url": "https://pbs.twimg.com/profile_images/1204157983954878464/PA_8-IF5_normal.jpg",
            "protected": False,
            "publis_metrics": {
                "followers_count": 419675,
                "following_count": 1055,
                "listed_count": 5555,
                "tweet_count": 108856
            },
            "url": "http://t.co/Z4sBQwWTQT",
            "username": "REI",
            "verified": True
        }
    ]
    # results = {
    #     "415859364": {
    #         "created_at":"Fri Nov 18 22:31:18 +0000 2011",
    #         "description":"#BlackLivesMatter",
    #         "favourites_count":6988,
    #         "followers_count":8313604,
    #         "following_count":116,
    #         "id":"415859364",
    #         "location":"Beaverton, Oregon",
    #         "media_count":3104,
    #         "name":"Nike",
    #         "profile_banner_url":"https://pbs.twimg.com/profile_banners/415859364/1516124378",
    #         "profile_image_url_https":"https://pbs.twimg.com/profile_images/953320896101412864/UdE5mfkP_normal.jpg",
    #         "statuses_count":36869,
    #         "username":"Nike",
    #     },
    # }
    return users