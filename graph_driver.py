from neo4j import GraphDatabase
from dotenv import dotenv_values
from soup_models import Document
from collections import defaultdict

config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}

class GraphDBDriver:
    """
    Main methods:
        query_node_dict: Query database by a node dictionary
        query: makes a direct cypher query
        upload_nodes: Upload an iterable of nodes to the database

    """
    def __init__(self, uri=config["LOCAL_GRAPH_URI"], user=config["LOCAL_GRAPH_USER"], password=config["LOCAL_GRAPH_PWD"]):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            print("Failed to create the driver:", e)
        # self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self.driver:
            self.driver.close()

    # def upload_test(self):
    #     assert self.driver, "Driver not initialized!"
    #     with self.driver.session() as session:
    #         return session.write_transaction(self._create_node, self._node_dict_to_cypher({'type': "Document", 'title': "test1"}))

    # Query Methods
    def query_node_dict(self, node_dict):
        return self.query("MATCH " + self._node_dict_to_cypher(node_dict) + " RETURN node")
    
    def query_node(self, node):
#         print("MATCH (node:{} {{key: \"{}\"}}) RETURN node".format(node.type, node.key))
        return self.query("MATCH (node:{} {{key: \"{}\"}}) RETURN node".format(node.type, node.key))

    def query(self, query, db=None):
        assert self.driver, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.driver.session(database=db) if db is not None else self.driver.session() 
            response = list(session.run(query))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session:
                session.close()
        return response

    # Upload Methods
    def upload_nodes(self, nodes):
        assert self.driver, "Driver not initialized!"
        with self.driver.session() as session:
            ret = []
            for node in nodes:
                exists = list(session.run("MATCH (node:{} {{key: \"{}\"}}) RETURN node".format(node.type, node.key)))
                if len(exists) == 0:
                    # assert type(doc) == Document , "Error: non-Document node passed to doc upload function"
                    ret.append(session.write_transaction(self._create_and_return_node, node.to_dict()))
                    print("Uploaded", ret[-1])
                else:
                    print(node.key, "already exists in database")
            return ret

    @staticmethod
    def _create_and_return_node(tx, node_dict):
        cypherquery = ["CREATE (node:{})".format(node_dict['type'])]
        for key in node_dict.keys():
            cypherquery.append("SET node.{} = ${}".format(key, key))
        cypherquery.append("RETURN node.title + ' at ID:' + id(node)")
#         print(" ".join(cypherquery))
        result = tx.run(" ".join(cypherquery), node_dict)
        return result.single()[0]

    # Helper Methods
    """
    Converts a node in dictionary form to a cypher create query
    """
    @staticmethod
    def _node_dict_to_cypher(node, name="node"):
        assert type(node) in [dict, defaultdict]
        query = "({}:{} {{".format(name, node['type'])
        properties = []
        for key, value in node.items():
            properties.append("{}:\"{}\"".format(key, value))
        props = ", ".join(properties)
        end_query = "})"
        return query + props + end_query

if __name__ == "__main__":  
    # greeter = HelloWorldExample("bolt://localhost:7687", "neo4j", "neo4j")
    print("Testing Graph Driver...")
    driver = GraphDBDriver(config["LOCAL_GRAPH_URI"], config["LOCAL_GRAPH_USER"], config["LOCAL_GRAPH_PWD"])
    print("Querying all nodes")
    print(driver.query("MATCH (n) return n"))
    print("Uploading one node")
    tweet = Document("test1", "title", "tweet")
    driver.upload_nodes([tweet])
    print("Querying single node")
    print(driver.query_node(tweet))
    print("Uploading several nodes with pre-existing in database")
    tweets = [tweet, Document("test2", "title", "tweet"), Document("test3", "title", "tweet")]
    driver.upload_nodes(tweets)
    driver.close()
    print("Finished")