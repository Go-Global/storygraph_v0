import networkx as nx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout
from pyvis.network import Network
import matplotlib.pyplot as plt
import random

# Story Graph Class
class Graph: 
    def __init__(self, title, directed=True): 
        self.net = Network(directed=directed, heading=title)
        self.net.width = '1500px'
        self.net.height = '600px'
        self.root = None

    # def setRoot(self, root):
    #     self.root = root

    # def getRoot(self):
    #     if self.root:
    #         return self.root
    #     elif len(self.nodes > 0):
    #         return self.nodes[0]
    #     else:
    #         print("Error: No nodes in graph")
    #         return None

    def addNode(self, genericNode):
        self.net.add_node(
                genericNode.id, 
                label=genericNode.label,
                shape=genericNode.shape,
                title=genericNode.text)#, size=size)

    def addNodeManually(self, id, label=None, text=None, shape='dot', size=50):
        # if self.net.get_node(id):
        #     print("Error: id {} already exists in network".format(id))
        #     return None

        self.net.add_node(id, label=label, shape=shape, title=text)#, size=size)

    def addEdge(self, id_a, id_b, label=None): 
        # assert self.net.get_node(id_a) and self.net.get_node(id_b), "Error: adding edge to unknown node(s)" 
        self.net.add_edge(id_a, id_b, label=label)

    def addEdges(self, edgeList, add=True):
        for a, b in edgeList:
            self.addEdge(a, b, add)

    def addNodes(self, genericNodeList):
        for node in genericNodeList:
            self.addNode(node)

    def visualize(self, name="example"): 
        # pos = hierarchy_pos(G, self.getRoot())
        # print(pos)
        # nx.draw(G, pos=pos, with_labels=True)
        # plt.savefig('hierarchy.png')
        # plt.show()
        # net.from_nx(G)
        # self.net.show_buttons(filter_=['layout', 'physics', 'nodes', 'edges'])
        # self.net.show_buttons()
        self.net.set_options("""var options = {
            "edges": {
                "color": {
                "inherit": true
                },
                "smooth": false
            },
            "physics": {
                "hierarchicalRepulsion": {
                "centralGravity": 0
                },
                "minVelocity": 0.75,
                "solver": "hierarchicalRepulsion"
            }
            }""")
        self.net.show(name + ".html")

class GenericNode:
    def __init__(self, id, label=None, text=None):
        self.id = id
        self.label = label if label else self.id 
        self.text = text
        self.shape='dot'


class HierarchalGraph: 
   
    def __init__(self, title, directed=True, hierarchal=True): 
        self.net = Network(directed=directed, layout=hierarchal, heading=title)
        self.net.width = '1500px'
        self.net.height = '600px'
        self.root = None

    # def setRoot(self, root):
    #     self.root = root

    # def getRoot(self):
    #     if self.root:
    #         return self.root
    #     elif len(self.nodes > 0):
    #         return self.nodes[0]
    #     else:
    #         print("Error: No nodes in graph")
    #         return None

    def addNode(self, genericHierarchalNode):
        self.net.add_node(
                genericHierarchalNode.id, 
                label=genericHierarchalNode.label,
                level=genericHierarchalNode.level,
                shape=genericHierarchalNode.shape,
                title=genericHierarchalNode.text)#, size=size)

    def addNodeManually(self, id, level=None, label=None, text=None, shape='dot', size=50):
        # if self.net.get_node(id):
        #     print("Error: id {} already exists in network".format(id))
        #     return None

        self.net.add_node(id, label=label, level=level, shape=shape, title=text)#, size=size)

    def addEdge(self, id_a, id_b, label=None): 
        # assert self.net.get_node(id_a) and self.net.get_node(id_b), "Error: adding edge to unknown node(s)" 
        self.net.add_edge(id_a, id_b, label=label)

    def addEdges(self, edgeList, add=True):
        for a, b in edgeList:
            self.addEdge(a, b, add)

    def addNodes(self, genericNodeList):
        for node in genericNodeList:
            self.addNode(node)

    def visualize(self, name="example"): 
        # pos = hierarchy_pos(G, self.getRoot())
        # print(pos)
        # nx.draw(G, pos=pos, with_labels=True)
        # plt.savefig('hierarchy.png')
        # plt.show()
        # net.from_nx(G)
        # self.net.show_buttons(filter_=['layout', 'physics', 'nodes'])
        self.net.set_options("""var options = {
            "nodes": {
                "font": {
                "size": 30
                }
            },
            "layout": {
                "hierarchical": {
                "enabled": true,
                "levelSeparation": 175,
                "nodeSpacing": 230,
                "treeSpacing": 205
                }
            },
            "physics": {
                "hierarchicalRepulsion": {
                "centralGravity": 0,
                "nodeDistance": 175
                },
                "minVelocity": 0.75,
                "solver": "hierarchicalRepulsion"
            }
            }""")
        self.net.show(name + ".html")

class GenericHierarchalNode:
    def __init__(self, id, level):
        self.id = id
        self.level = level
        self.label = self.id
        self.text = None
        self.shape='dot'
    
# # Needed for visualization (thanks https://stackoverflow.com/questions/29586520/can-one-get-hierarchical-graphs-from-networkx-with-python-3)  
# def hierarchy_pos(G, root=None, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5):

#     '''
#     From Joel's answer at https://stackoverflow.com/a/29597209/2966723.  
#     Licensed under Creative Commons Attribution-Share Alike 
    
#     If the graph is a tree this will return the positions to plot this in a 
#     hierarchical layout.
    
#     G: the graph (must be a tree)
    
#     root: the root node of current branch 
#     - if the tree is directed and this is not given, 
#       the root will be found and used
#     - if the tree is directed and this is given, then 
#       the positions will be just for the descendants of this node.
#     - if the tree is undirected and not given, 
#       then a random choice will be used.
    
#     width: horizontal space allocated for this branch - avoids overlap with other branches
    
#     vert_gap: gap between levels of hierarchy
    
#     vert_loc: vertical location of root
    
#     xcenter: horizontal location of root
#     '''
#     if not nx.is_tree(G):
#         raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

#     if root is None:
#         if isinstance(G, nx.DiGraph):
#             root = next(iter(nx.topological_sort(G)))  #allows back compatibility with nx version 1.11
#         else:
#             root = random.choice(list(G.nodes))

#     def _hierarchy_pos(G, root, width=1., vert_gap = 0.2, vert_loc = 0, xcenter = 0.5, pos = None, parent = None):
#         '''
#         see hierarchy_pos docstring for most arguments

#         pos: a dict saying where all nodes go if they have been assigned
#         parent: parent of this branch. - only affects it if non-directed

#         '''
    
#         if pos is None:
#             pos = {root:(xcenter,vert_loc)}
#         else:
#             pos[root] = (xcenter, vert_loc)
#         children = list(G.neighbors(root))
#         if not isinstance(G, nx.DiGraph) and parent is not None:
#             children.remove(parent)  
#         if len(children)!=0:
#             dx = width/len(children) 
#             nextx = xcenter - width/2 - dx/2
#             for child in children:
#                 nextx += dx
#                 pos = _hierarchy_pos(G,child, width = dx, vert_gap = vert_gap, 
#                                     vert_loc = vert_loc-vert_gap, xcenter=nextx,
#                                     pos=pos, parent = root)
#         return pos

            
#     return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)

def test_normal():
    G = Graph("Sentence Test")
    sentence = "hi my name is stef, this is my plot line"
    tokens = sentence.split(" ")
    for i, token in enumerate(tokens):
        G.addNodeManually(str(i)+token, label=token, text="hi")

    for i in range(len(tokens) - 1):
        G.addEdge(str(i) + tokens[i], str(i+1) + tokens[i+1])

    G.addNodeManually("2codename", label="codename")
    G.addEdge("1my", "2codename")
    G.addEdge("2codename", "3is")
    G.visualize()


def test_hierarchal():
    G = HierarchalGraph("Sentence Test")
    sentence = "hi my name is stef, this is my plot line"
    tokens = sentence.split(" ")
    for i, token in enumerate(tokens):
        G.addNodeManually(str(i)+token, label=token, level=i, text="hi")

    for i in range(len(tokens) - 1):
        G.addEdge(str(i) + tokens[i], str(i+1) + tokens[i+1])

    G.addNodeManually("2codename", label="codename", level=2)
    G.addEdge("1my", "2codename")
    G.addEdge("2codename", "3is")
    G.visualize()


if __name__ == "__main__":
    test_normal()