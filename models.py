import datetime
import neo4j

primitives = set([int, float, bool, datetime.datetime, str, list, neo4j.time.DateTime]) # Neo4j can only take primitive types or arrays

OUTPUT_PATH = "output/"

"""
Node Models (2/13/2022)
- Entities
- Interactions
- Attributes
"""
# Top level node class
class Node:
    def __init__(self, key, title, node_type, attrs=dict(), db_id=None):
        assert type(key) == str, "Error: key must be a string"
        self.key = key
        self.title = title
        self.type = node_type
        self.attrs = None
        self.set_attrs(attrs) # Attribute dictionary
        self.db_id = db_id # id from database. Populated when retrieving nodes
        
    def __str__(self):
        return "{}:{}".format(self.title, self.type)

    def set_attrs(self, attrs):
        attrs = flatten_json(attrs)
        for key, value in attrs.items():
            assert type(key) in primitives, "type " + str(type(key)) + " not supported by neo4j"
            assert type(value) in primitives, "type " + str(type(value)) + " not supported by neo4j"
        self.attrs = attrs
    
# Node for Entities
# is of node_type = 'entity', key is the text
class Entity(Node):
    def __init__(self, text, attrs=dict(), db_id=None):
        super().__init__(text, text, "entity", attrs=attrs, db_id=db_id)

# Node for Interactions
# is of node_type = 'interaction', key is text
class Interaction(Node):
    def __init__(self, text, attrs=dict(), db_id=None):
        super().__init__(text, text, "interaction", attrs=attrs, db_id=db_id)
        

# Node for Attribute (A news article or tweet)
# is of node_type = "document", key for tweets are its twitter id
class Attribute(Node):
    def __init__(self, text, text, doc_type, attrs=dict(), db_id=None):
        super().__init__(text, text, "attribute", attrs=attrs, db_id=db_id)


    def to_dict(self):
        output = self.attrs.copy()
        output['type'] = "document"
        output['key'] = self.key
        output['title'] = self.title
        output['db_id'] = self.db_id
        return output


"""
Edge-Related Models

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
