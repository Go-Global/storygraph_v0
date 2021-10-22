import datetime, os

from neo4j import GraphDatabase
from neo4j.data import Record
from dotenv import dotenv_values, load_dotenv
try:
    from .models import Node, Source, Entity, Action, Document, Authored, Interacts, Contains, References, Involved
except:
    print("Import error, assuming module called directly")
    from models import Node, Source, Entity, Action, Document, Authored, Interacts, Contains, References, Involved

# config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}
load_dotenv()
config = {
    'REMOTE_GRAPH_URI': os.getenv('REMOTE_GRAPH_URI'),
    'REMOTE_GRAPH_USER': os.getenv('REMOTE_GRAPH_USER'),
    'REMOTE_GRAPH_PWD': os.getenv('REMOTE_GRAPH_PWD'),
    'LOCAL_GRAPH_URI': os.getenv('LOCAL_GRAPH_URI'),
    'LOCAL_GRAPH_USER': os.getenv('LOCAL_GRAPH_USER'),
    'LOCAL_GRAPH_PWD': os.getenv('LOCAL_GRAPH_PWD'),
}
assert len(config) > 0, "Error: Cannot read .env file"

class GraphDBDriver:
    """
    Main methods:
        query_node_dict: Query database by a node dictionary
        query: makes a direct cypher query
        upload_nodes: Upload an iterable of nodes to the database
        upload_edges: Upload an iterable of edges to the database

    """
    def __init__(self, remote=False):
        if remote:
            uri = config["REMOTE_GRAPH_URI"]
            user = config["REMOTE_GRAPH_USER"]
            password = config["REMOTE_GRAPH_PWD"]
        else:
            uri = config["LOCAL_GRAPH_URI"]
            user = config["LOCAL_GRAPH_USER"]
            password = config["LOCAL_GRAPH_PWD"]

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            self.driver = None
            print("Failed to create the driver:", e) # TODO: Sometimes the driver is created succesfully but query fails with Cannot resolve address ___________

    def close(self):
        if self.driver:
            self.driver.close()

    # Query Methods (returns a list of neo4j.data.Records)
    def query_node_dict(self, node_dict, parse_nodes=True):
        return self.raw_query("MATCH " + self._node_dict_to_cypher(node_dict) + " RETURN node")
    
    def query_node(self, node, parse_nodes=True):
#         print("MATCH (node:{} {{key: \"{}\"}}) RETURN node".format(node.type, node.key))
        return self.raw_query("MATCH (node:{} {{key: \"{}\"}}) RETURN node".format(node.type, node.key), parse_nodes=parse_nodes)
    
    def query_nodes_by_id(self, id_list, parse_nodes=True):
        id_string = ",".join([str(id_) for id_ in id_list])
        query = 'MATCH (node) WHERE ID(node) in [{}] RETURN node'.format(id_string)
        return self.raw_query(query, parse_nodes=parse_nodes)    

    def query_edge(self, edge, parse_nodes=False):
        return self.raw_query("MATCH (a:{} {{key: \"{}\"}})-[edge:{}]->(b:{} {{key: \"{}\"}}) RETURN edge".format(edge.source_type, edge.source_key, edge.label, edge.dest_type, edge.dest_key), parse_nodes=False)

    # Returns a list of neo4j.data.Records
    def raw_query(self, query, parse_nodes=False):
        assert self.driver, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.driver.session()
            response = list(session.run(query))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session:
                session.close()
        if response is None:
            print("Warning: nothing returned for query:", query)
            return None
        if parse_nodes:
            return [self.record_to_models(record)['node'] for record in response]
        else:
            return response    

    # Semi-structured query
    # Returns a list of neo4j.data.Records
    def structured_query(self, MATCH=None, WHERE=None, RETURN=None, LIMIT=10, parse_nodes=False):
        query_arr = []
        if MATCH:
            query_arr.append("MATCH " + MATCH)
        if WHERE:
            query_arr.append("WHERE " + WHERE)
        if RETURN:
            query_arr.append("RETURN " + RETURN)
        if LIMIT:
            assert type(LIMIT) is int, "Error: LIMIT param must be an int not " + str(type(LIMIT))
            query_arr.append("LIMIT " + str(LIMIT))
        
        query = "\n".join(query_arr)
        # print(query)
        return self.raw_query(query, parse_nodes=parse_nodes)
        
    # Formats the 'WHERE' component of a Cypher Query from two datetimes and a target field name
    # Returns None if both start and end are empty
    def format_time_range(self, field_name, start=None, end=None):
        if not start and not end:
            return None
        tokens = []
        if start:
            assert type(start) is datetime.datetime, "Error: value passed in must be a datetime object"
            tokens.append("node." + field_name)
            tokens.append(">= localdatetime(datetime('{}'))".format(start.strftime("%Y-%m-%d")))
            if end:
                assert start < end, "Error: Invalid range between {} and {}".format(start, end)
                tokens.append("AND")
        if end:
            assert type(end) is datetime.datetime, "Error: value passed in must be a datetime object"
            tokens.append("node." + field_name)
            tokens.append("<= localdatetime(datetime('{}'))".format(end.strftime("%Y-%m-%d")))
        
        return " ".join(tokens)
            
    
    # Upload Methods
    # Node Methods
    def upload_nodes(self, nodes):
        assert self.driver, "Driver not initialized!"
        with self.driver.session() as session:
            ret = []
            count = 0
            for node in nodes:
                exists = list(session.run("MATCH (node:{} {{key: \"{}\"}}) RETURN node".format(node.type, node.key)))
                if len(exists) == 0:
                    # print("Attempting to upload", node.title, str(node.attrs))
                    # assert type(doc) == Document , "Error: non-Document node passed to doc upload function"
                    ret.append(session.write_transaction(self._create_and_return_node, node.to_dict()))
                    print("Uploaded", node.key)
                    count += 1
                else:
                    print(node.key, "already exists in database")
            print("Uploaded {} nodes out of {} total".format(count, len(nodes)))
            return ret

    @staticmethod
    def _create_and_return_node(tx, node_dict):
        cypherquery = ["CREATE (node:{})".format(node_dict['type'])]
        for key in node_dict.keys():
            cypherquery.append("SET node.{} = ${}".format(key, key))
        cypherquery.append("RETURN node")
#         print(" ".join(cypherquery))
        result = tx.run(" ".join(cypherquery), node_dict)
        entry = result.single()        
        return entry['node'] if entry else None

    # Edges Methods
    def upload_edges(self, edges):
        assert self.driver, "Driver not initialized!"
        with self.driver.session() as session:
            ret = []
            count = 0
            for edge in edges:
                exists = list(session.run("MATCH (a:{} {{key: \"{}\"}})-[edge:{}]->(b:{} {{key: \"{}\"}}) RETURN edge".format(edge.source_type, edge.source_key, edge.label, edge.dest_type, edge.dest_key)))
                if len(exists) == 0:
                    # assert type(doc) == Document , "Error: non-Document node passed to doc upload function"
                    ret.append(session.write_transaction(self._create_and_return_edge, edge.to_dict(), edge.source_key, edge.dest_key))
                    print("Uploaded", str(edge))
                    count += 1
                else:
                    print(str(edge), "already exists in database")
            print("Uploaded {} edges out of {} total".format(count, len(edges)))
            return ret

    @staticmethod
    def _create_and_return_edge(tx, edge_dict, source_key, dest_key):
        cypherquery = ["MATCH (a), (b)", "WHERE a.key=\"{}\" AND b.key = \"{}\"".format(source_key, dest_key), "CREATE (a)-[edge:{}]->(b)".format(edge_dict['label'])]
        for key in edge_dict.keys():
            cypherquery.append("SET edge.{} = ${}".format(key, key))
        cypherquery.append("RETURN edge")
#         print(" ".join(cypherquery))
        result = tx.run(" ".join(cypherquery), edge_dict)
        # print(result)
        entry = result.single()        
        return entry['edge'] if entry else None

    # Helper Methods   
    """
    Converts a node in dictionary form to a cypher create query
    """
    @staticmethod
    def _node_dict_to_cypher(node, name="node"):
        assert type(node) in [dict]
        query = "({}:{} {{".format(name, node['type'])
        properties = []
        for key, value in node.items():
            properties.append("{}:\"{}\"".format(key, value))
        props = ", ".join(properties)
        end_query = "})"
        return query + props + end_query

    """
    Converts a returned object to a dictionary of Node or Edge from Soup Models
    """
    @staticmethod
    def record_to_models(record):
        assert type(record) == Record
        assert 'node' in record.keys() or 'edge' in record.keys(), "Neither node or edge found in record keys: " + str(record.keys())
        ret = dict()
        def node_to_model(node):
            # print(node.id)
            # print(node.keys())
            if node['type'] == 'entity':
                return Entity(node['key'], attrs=dict(node))
            elif node['type'] == 'action':
                return Action(node['key'], attrs=dict(node))
            elif node['type'] == 'source':
                return Source(node['key'], node['name'], node['source_type'], attrs=dict(node), date_processed=node['date_processed'], db_id=node.id)
            elif node['type'] == 'document':
                return Document(node['key'], node['title'], node['doc_type'], attrs=dict(node), date_processed=node['date_processed'], db_id=node.id)
            else:
                print("ERROR: unrecognized node type:", node['type'])

        # Process Node
        if 'node' in record.keys():
            assert record['node']['type'] in ['entity', 'action', 'source', 'document'], "Error: unidentified node type " + record['node']['type']
            node = node_to_model(record['node'])
            if node:
                ret['node'] = node
        
        # TODO: This part can probably be greatly optimized since I am building two new node objects for every edge
        # Process Edge
        if 'edge' in record.keys():
            assert record['edge']['label'] in ['contains', 'authored', 'interacts', 'references', 'involved'], "Error: unidentified edge type " + record['edge']['label']
            edge = record['edge']
            # source, dest = node_to_model(edge.nodes[0]), node_to_model(edge.nodes[1])
            # if edge['label'] == 'contains':
            #     ret['edge'] = Contains(source, dest)
            # elif edge['label'] == 'authored':
            #     ret['edge'] = Authored(source, dest)
            # elif edge['label'] == 'interacts':
            #     ret['edge'] = Interacts(source, dest, edge['interaction_type'])
            # elif edge['label'] == 'references':
            #     ret['edge'] = References(source, dest)
            # elif edge['label'] == 'involved':
            #     ret['edge'] = Involved(source, dest)
            ret['edge'] = (edge['label'], edge['source_key'], edge['dest_key'])
        
        return ret

if __name__ == "__main__":  
    # greeter = HelloWorldExample("bolt://localhost:7687", "neo4j", "neo4j")
    print("Testing Graph Driver...")
    driver = GraphDBDriver(remote=False)
    ret = driver.raw_query("MATCH (node)-[edge:interacts]->() RETURN node, edge LIMIT 10", parse_nodes=True)
    print([str(r) for r in ret])

    print("Test date-constrained querying")
    # print(driver.format_time_range("created_at", start=datetime.datetime(2021, 7, 1), end=datetime.datetime.now()))
    # print(driver.format_time_range("created_at", start=None, end=datetime.datetime.now()))
    # print(driver.format_time_range("created_at", start=datetime.datetime.now(), end=None))
    ret = driver.structured_query(MATCH="(node:document)", WHERE=driver.format_time_range('created_at', end=datetime.datetime.now()), RETURN="node", parse_nodes=True)
    print([str(r) for r in ret])
    # print("Querying all nodes")
    # print(driver.query("MATCH (n) return n"))
    print("Uploading nodes")
    tweet1 = Document("test_tweet1", "title", "tweet")
    source = Source("test_source1", "title", "source")
    driver.upload_nodes([tweet1, source])
    print("Adding connecting Edge")
    edge = Interacts(source, tweet1, "follows")
    driver.upload_edges([edge])
        
    print("Querying single node")
    result = driver.query_node(tweet1)
    print(result)
    result1 = driver.query_edge(edge) # Does not support parsing yet
    print(result1)
    print("Uploading several nodes with pre-existing in database")
    tweets = [tweet1, Document("test2", "title", "tweet"), Document("test3", "title", "tweet")]
    # driver.upload_nodes(tweets)
    print("Querying nodes by list of DB IDs")
    nodes_by_id = driver.query_nodes_by_id([1, 2, 3, 4, 5, 6, 7, 10, 550, 1000], parse_nodes=True)
    print([str(r) for r in nodes_by_id])

    print("Cleaning up")
    driver.raw_query("MATCH (n:document) WHERE n.key=\"test_tweet1\" DETACH DELETE n")
    driver.raw_query("MATCH (n:source) WHERE n.key=\"test_source1\" DETACH DELETE n")
    print("Deleted nodes")
    driver.close()
    print("Finished")
    