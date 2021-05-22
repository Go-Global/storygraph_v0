from collections import defaultdict
from displaygraphs import Graph, GenericNode
# from prgraph import DocumentNode
import networkx as nx
import datetime

"""
StoryGraph Model
"""
OUTPUT_PATH = "output/"
class StoryGraph:
    # This class defines a story graph 'soup' of entities and actions
    def __init__(self, title="default"):
        self.title = title # Title of the storygraph
        self.node_dict = dict() # dictionary of keys to nodes (for example, spacy tokens -> Nodes)
        self.nodes = set() # might change to set
        self.edges = set() # might change to set
        self.display_graph = None
    
    def read_node_dict(self, node_dict):
        assert type(node_dict) in [dict, defaultdict]
        self.node_dict = node_dict
        self.nodes = set([node for _, node in self.node_dict.items()])

    def read_edge_set(self, edges):
        assert type(edges) == set
        self.edges = edges

    def build_display_graph(self):
        print("Building Display Graph")
        self.display_graph = Graph(self.title)
        nodes = []
        nodecount = 0
        token_to_idx = dict()
        for node in self.nodes:

            nodes.append(GenericNode(nodecount, label=node.title, text=str(dict(node.attrs))))
            token_to_idx[node] = nodecount
            nodecount += 1

        self.display_graph.addNodes(nodes)
        
        edges = [rel.tup() for rel in self.edges]
        for name, src, dst in edges:
            if src in token_to_idx.keys() and dst in token_to_idx.keys():
                self.display_graph.addEdge(token_to_idx[src], token_to_idx[dst], label=name)
            else:
                print("Couldn't match relation between", src, dst)
        # print(token_to_idx)
        # G.visualize(self.title)
        # return G.net
    
    def write_graph_ml(self):
        print("Writing graphml to", OUTPUT_PATH + self.title + ".xml")
        if not self.display_graph:
            self.build_display_graph()
        nxGraph = pyviz_to_nx(self.display_graph.net)
        nx.write_graphml(nxGraph, OUTPUT_PATH + self.title + ".xml")

    def visualize(self):
        print("Visualizing Graph")
        # print(self.nodes)
        # print(self.node_dict)
        # print(self.edges)
        
        if not self.display_graph:
            self.build_display_graph()
        self.display_graph.visualize(OUTPUT_PATH + self.title)

# Helper method
def pyviz_to_nx(net):
    G = nx.Graph()
    G.add_nodes_from([(attrs['id'], attrs) for attrs in net.nodes])
    G.add_edges_from([(attrs['from'], attrs['to'], attrs) for attrs in net.edges])
    return G

"""
Node-Related Models
- Narrative Entities
- Actions (Any verb in text basically)
- Actual Sources ("Trump's Twitter Account", Donald Trump himself, NYTimes)
- Documents (A news article or tweet)
"""
# Top level node class
class Node:
    def __init__(self, key, title, node_type, attrs=defaultdict(lambda: set())):
        self.key = key
        self.title = title
        self.type = node_type
        self.attrs = attrs # Attribute dictionary
        
    def __str__(self):
        return self.title
    
# Node for Narrative Entities
# is of node_type = 'entity', key is a spacy token, and also contains an optional span object for compound nodes
class Entity(Node):
    def __init__(self, root_token, attrs=defaultdict(lambda: set())):
        super().__init__(root_token, root_token.text, "entity", attrs=attrs)
        self.span = None # Either a span object or a list of tokens. TODO: pick one.

# Node for Narrative Actions
# is of node_type = 'action', key is a spacy token, and also contains an optional span object for compound nodes
class Action(Node):
    def __init__(self, root_token, attrs=defaultdict(lambda: set())):
        super().__init__(root_token, root_token.text, "action", attrs=attrs)
        # self.span = None # Either a span object or a list of tokens. TODO: pick one.

# Node for Actual Sources  ("Trump's Twitter Account", Donald Trump himself, NYTimes)
# is of node_type = 'source', key is a , and also contains an optional span object for compound nodes
class Source(Node):
    def __init__(self, url, name, source_type, attrs=defaultdict(lambda: set())):
        super().__init__(url, name, "source", attrs=attrs)
        self.source_type = source_type # Twitter account, Journalist, News Outlet, etc.
        # self.date_processed = date_processed if date_processed else datetime.datetime.now()

    def to_dict(self):
        output = self.attrs.copy()
        output['type'] = "source"
        output['key'] = self.url
        output['title'] = self.name
        output['name'] = self.name
        output['source_type'] = self.source_type
        # output['date_processed'] = self.date_processed
        return output

# Node for Documents (A news article or tweet)
# is of node_type = "document", key is tentatively a url, and also contains an optional span object for compound nodes
class Document(Node):
    def __init__(self, key, title, doc_type, attrs=defaultdict(lambda: set()), spacy_doc=None, date_processed=None):
        super().__init__(key, title, "document", attrs=attrs)
        self.doc_type = doc_type # tweet, article, etc.
        self.doc_obj = spacy_doc # Spacy doc object
        self.date_processed = date_processed if date_processed else datetime.datetime.now()

    def to_dict(self):
        output = self.attrs.copy()
        output['type'] = "document"
        output['key'] = self.key
        output['title'] = self.title
        output['doc_type'] = self.doc_type
        output['doc_obj'] = self.doc_obj
        output['date_processed'] = self.date_processed
        return output




"""
Edge-Related Models
- **Contains (Doc → Entity, Doc → Action)
- **Authored (Source → Doc)
- **Follows/Likes (Source → Source/Doc) Indicates how sources pay attention to each other / other documents
- **References (Doc → Source/Doc) Indicates how a document refers to a real world source/person or other document
- Coreference (Entity → Source/Doc) Much harder. Inferring referents using NLP. Can be used to expand references.
- Sequence (Action → Action) sequence of actions in the same document
- Involved (Narrative Entity → Action)
"""
# Top level edge class
class Edge:
    def __init__(self, label, source, dest, timestamp=0):
        self.label = label
        self.source = source
        self.dest = dest
        self.attrs = defaultdict(lambda: set()) # Attribute dictionary
        self.time = datetime.date.fromtimestamp(timestamp)
        self.attrs['time'] = self.time
        
    def tup(self):
        return self.label, self.source, self.dest
    
#     def __iter__(self):
#         return iter()
    
    def __str__(self):
        return str((self.label, self.source.text, self.dest.text))


class Contains(Edge):
    # (Doc → Entity, Doc → Action)
    def __init__(self, source, dest, timestamp=0):
        assert source.type in ["document"] and dest.type in ['entity', 'action'], "Failed node type assert for contains edge between {} and {}".format(str(source), str(dest))
        super().__init__("contains", source, dest, timestamp=timestamp)

class Authored(Edge):
    # (Source → Doc)
    def __init__(self, source, dest, timestamp=0):
        assert source.type in ["source"] and dest.type in ["document"], "Failed node type assert for contains edge between {} and {}".format(str(source), str(dest))
        super().__init__("authored", source, dest, timestamp=timestamp)

class Interacts(Edge):
    # (Source → Source/Doc) Indicates how sources pay attention to each other / other documents
    def __init__(self, source, dest, timestamp=0):
        assert source.type in ["source"] and dest.type in ['source', "document"], "Failed node type assert for contains edge between {} and {}".format(str(source), str(dest))
        super().__init__("interacts", source, dest, timestamp=timestamp)

class References(Edge):
     # (Doc → Source/Doc) Indicates how a document refers to a real world source/person or other document
     def __init__(self, source, dest, timestamp=0):
        assert source.type in ["document"] and dest.type in ['source', "document"], "Failed node type assert for contains edge between {} and {}".format(str(source), str(dest))
        super().__init__("references", source, dest, timestamp=timestamp)

class Involved(Edge):
     # (Narrative Entity → Action)
     def __init__(self, source, dest, timestamp=0):
         # The assert needs work. I have entities referring to each other in the soup extractor
        assert source.type in ["entity", 'action'] and dest.type in ['action', 'entity'], "Failed node type assert for contains edge between {} and {}".format(str(source), str(dest))
        super().__init__("involved", source, dest, timestamp=timestamp)