# Takes in twitter data and parses it into storygraph schema
import datetime

from graph_driver import GraphDBDriver
from soup_models import StoryGraph, Source, Document, Authored, Interacts, References

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

def get_users():
    results = {
        "415859364": {
            "created_at":"Fri Nov 18 22:31:18 +0000 2011",
            "description":"#BlackLivesMatter",
            "favourites_count":6988,
            "followers_count":8313604,
            "following_count":116,
            "id":"415859364",
            "location":"Beaverton, Oregon",
            "media_count":3104,
            "name":"Nike",
            "profile_banner_url":"https://pbs.twimg.com/profile_banners/415859364/1516124378",
            "profile_image_url_https":"https://pbs.twimg.com/profile_images/953320896101412864/UdE5mfkP_normal.jpg",
            "statuses_count":36869,
            "username":"Nike",
        },
    }
    return results

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

if __name__ == '__main__':
    # class Source(Node)  __init__(self, url, name, source_type, attrs=defaultdict(lambda: set()))
    # class Document(Node) __init__(self, key, title, doc_type, attrs=defaultdict(lambda: set()), spacy_doc=None, date_processed=None)
    # class AllEdges(Edge) __init__(self, source, dest, timestamp=0)

    print("Testing Twitter Parser...")
    
    # Get Tweets
    tweet_nodes = get_twitter_nodes()

    # Get Users (check if exists in graph database first)
    driver = GraphDBDriver()
    driver.upload_docs(tweet_nodes)
    driver.close()

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

