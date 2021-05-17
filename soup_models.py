from collections import defaultdict
from displaygraphs import Graph, GenericNode
# from prgraph import DocumentNode
import networkx as nx
import datetime

OUTPUT_PATH = "output/"
class StoryGraph:
    # This class defines a story graph 'soup' of entities and actions
    def __init__(self, title="default"):
        self.title = title # Title of the storygraph
        self.node_dict = dict() # dictionary of keys to nodes (for example, spacy tokens -> Nodes)
        self.nodes = set() # might change to set
        self.edges = set() # might change to set
        self.display_graph = None
    
    def read_node_dict(self):
        self.nodes = set([node for _, node in self.node_dict.items()])

    def build_display_graph(self):
        print("Building Display Graph")
        self.display_graph = Graph(self.title)
        nodes = []
        nodecount = 0
        token_to_idx = dict()
        for node in self.nodes:

            nodes.append(GenericNode(nodecount, label=node.text, text=str(dict(node.attrs))))
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

class Node:
    def __init__(self, root_token, node_type):
        self.root_token = root_token
        self.span = None # Either a span object or a list of tokens. TODO: pick one.
        self.type = node_type
        self.text = root_token.text
        self.attrs = defaultdict(lambda: set()) # Attribute dictionary
        
    def __str__(self):
        return self.text
    
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
