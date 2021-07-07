import datetime
import neo4j

primitives = set([int, float, bool, datetime.datetime, str, list, neo4j.time.DateTime]) # Neo4j can only take primitive types or arrays

OUTPUT_PATH = "output/"

"""
Node-Related Models
- Narrative Entities
- Actions (Any verb in text basically)
- Actual Sources ("Trump's Twitter Account", Donald Trump himself, NYTimes)
- Documents (A news article or tweet)
"""
# Top level node class
class Node:
    def __init__(self, key, title, node_type, attrs=dict()):
        assert type(key) == str, "Error: key must be a string"
        self.key = key
        self.title = title
        self.type = node_type
        self.attrs = None
        self.set_attrs(attrs) # Attribute dictionary
        
    def __str__(self):
        return "{}:{}".format(self.title, self.type)

    def set_attrs(self, attrs):
        attrs = flatten_json(attrs)
        for key, value in attrs.items():
            assert type(key) in primitives, "type " + str(type(key)) + " not supported by neo4j"
            assert type(value) in primitives, "type " + str(type(value)) + " not supported by neo4j"
        self.attrs = attrs
    
# Node for Narrative Entities
# is of node_type = 'entity', key is a spacy token, and also contains an optional span object for compound nodes
class Entity(Node):
    def __init__(self, root_token, attrs=dict()):
        super().__init__(root_token, root_token.text, "entity", attrs=attrs)
        self.span = None # Either a span object or a list of tokens. TODO: pick one.

# Node for Narrative Actions
# is of node_type = 'action', key is a spacy token, and also contains an optional span object for compound nodes
class Action(Node):
    def __init__(self, root_token, attrs=dict()):
        super().__init__(root_token, root_token.text, "action", attrs=attrs)
        # self.span = None # Either a span object or a list of tokens. TODO: pick one.

# Node for Actual Sources  ("Trump's Twitter Account", Donald Trump himself, NYTimes)
# is of node_type = 'source', key is a , and also contains an optional span object for compound nodes
class Source(Node):
    def __init__(self, key, name, source_type, attrs=dict(), date_processed=None):
        super().__init__(key, name, "source", attrs=attrs)
        self.source_type = source_type # Twitter account, Journalist, News Outlet, etc.
        self.date_processed = date_processed if date_processed else datetime.datetime.now()

    def to_dict(self):
        output = self.attrs.copy()
        output['type'] = "source"
        output['key'] = self.key
        output['name'] = self.title
        output['source_type'] = self.source_type
        # output['date_processed'] = self.date_processed
        return output

# Node for Documents (A news article or tweet)
# is of node_type = "document", key is tentatively a url, and also contains an optional span object for compound nodes
class Document(Node):
    def __init__(self, key, title, doc_type, attrs=dict(), spacy_doc=None, date_processed=None):
        super().__init__(key, title, "document", attrs=attrs)
        self.doc_type = doc_type # tweet, article, etc.
        # self.doc_obj = spacy_doc # Spacy doc object-
        self.date_processed = date_processed if date_processed else datetime.datetime.now()
        self.nlp_processed = False # When a document is processed into entities and actions, this boolean is set to true

    def to_dict(self):
        output = self.attrs.copy()
        output['type'] = "document"
        output['key'] = self.key
        output['title'] = self.title
        output['doc_type'] = self.doc_type
        # output['doc_obj'] = self.doc_obj
        output['date_processed'] = self.date_processed
        output['nlp_processed'] = self.nlp_processed
        return output


"""
Edge-Related Models
- **Contains (Doc → Entity, Doc → Action)
- **Authored (Source → Doc)
- **Interacts Follows/Likes (Source → Source/Doc) Indicates how sources pay attention to each other / other documents
- **References (Doc → Source/Doc) Indicates how a document refers to a real world source/person or other document
- Coreference (Entity → Source/Doc) Much harder. Inferring referents using NLP. Can be used to expand references.
- Sequence (Action → Action) sequence of actions in the same document
- Involved (Narrative Entity → Action)
"""
# Top level edge class
# For source & dest, you can either pass in a Node object or tuple of (key, type)
class Edge:
    def __init__(self, label, source, dest, timestamp=0):
        self.label = label
        if type(source) == tuple:
            self.source_key, self.source_type = source
        else:
            self.source_key, self.source_type = source.key, source.type
        if type(dest) == tuple:
            self.dest_key, self.dest_type = dest
        else:
            self.dest_key, self.dest_type = dest.key, dest.type
        self.attrs = dict() # Attribute dictionary
        self.time = datetime.date.fromtimestamp(timestamp)
        self.attrs['time'] = self.time
        assert type(self.source_key) == str, "Error: source key must be a string"
        assert type(self.dest_key) == str, "Error: dest key must be a string"
        
    def tup(self):
        return self.label, self.source_key, self.dest_key
    
#     def __iter__(self):
#         return iter()
    
    def __str__(self):
        return str((self.label, str(self.source_key), str(self.dest_key)))

    def to_dict(self):
        output = self.attrs.copy()
        output['label'] = self.label
        output['source_key'] = self.source_key
        output['source_type'] = self.source_type
        output['dest_key'] = self.dest_key
        output['dest_type'] = self.dest_type
        return output
    
    def set_attrs(self, attrs):
        attrs = flatten_json(attrs)
        for key, value in attrs.items():
            assert type(key) in primitives, "type " + str(type(key)) + " not supported by neo4j"
            assert type(value) in primitives, "type " + str(type(value)) + " not supported by neo4j"
        self.attrs = attrs


class Contains(Edge):
    # (Doc → Entity, Doc → Action)
    def __init__(self, source, dest, timestamp=0):
        super().__init__("contains", source, dest, timestamp=timestamp)
        assert self.source_type in ["document"] and self.dest_type in ['entity', 'action'], "Failed node type assert for contains edge between {} and {}".format(str(source), str(dest))

class Authored(Edge):
    # (Source → Doc)
    def __init__(self, source, dest, timestamp=0):
        super().__init__("authored", source, dest, timestamp=timestamp)
        assert self.source_type in ["source"] and self.dest_type in ['document'], "Failed node type assert for authored edge between {} and {}".format(str(source), str(dest))

class Interacts(Edge):
    # (Source → Source/Doc) Indicates how sources pay attention to each other / other documents
    def __init__(self, source, dest, interaction_type, timestamp=0):
        super().__init__("interacts", source, dest, timestamp=timestamp)
        assert self.source_type in ["source"] and self.dest_type in ['source','document'], "Failed node type assert for interacts edge between {} and {}".format(str(source), str(dest))
        self.attrs['interaction_type'] = interaction_type

class References(Edge):
     # (Doc → Source/Doc) Indicates how a document refers to a real world source/person or other document
     def __init__(self, source, dest, timestamp=0):
        super().__init__("references", source, dest, timestamp=timestamp)
        assert self.source_type in ["document"] and self.dest_type in ['source', 'document'], "Failed node type assert for references edge between {} and {}".format(str(source), str(dest))

class Involved(Edge):
     # (Narrative Entity → Action)
     def __init__(self, source, dest, timestamp=0):
         # The assert needs work. I have entities referring to each other in the soup extractor
        super().__init__("involved", source, dest, timestamp=timestamp)
        assert self.source_type in ["entity", 'action'] and self.dest_type in ['action', 'entity'], "Failed node type assert for involved edge between {} and {}".format(str(source), str(dest))

# Helper Methods
def flatten_json(y):
    out = dict()

    def flatten(x, name=''):
        if type(x) is dict:
            # print("Flattening", x)
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out
