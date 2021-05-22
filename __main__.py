from twitter_parser import get_users, get_tweets

""" 
    Main function of soup parser and uploader
    Flow:
        Call Twitter API, format results into soup Nodes and Edges
        Upload to graphDB


"""
if __name__ == '__main__':
    get_twitter_nodes()