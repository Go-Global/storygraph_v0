#!/usr/bin/env python
# coding: utf-8

import sys
import spacy
from spacy import displacy
import re
from collections import defaultdict
import datetime
import neuralcoref
import networkx as nx
from networkx import write_graphml

from displaygraphs import HierarchalGraph, Graph
from soup_models import Node, Entity, Action, Edge, Involved, StoryGraph, pyviz_to_nx

# Combine list dictionaries (for attribute dictionaries)
def merge_attr_dicts(current, new):
    for key, values in new.items():
        if key in current.keys():
            current[key] = current[key] + values
        else:
            current[key] = values
    return current


# Merges compound tokens into the same entity
def merge_nodes(token_list, entity_dict):
    assert type(token_list[0]) == spacy.tokens.token.Token, "Error, wrong type passed to node merger" + type(token_list[0])
    merged_node = Entity(token_list[0])
    merged_node.span = token_list
    if type(token_list) == spacy.tokens.span.Span:
        merged_node.text = token_list.text
    else:
        merged_node.text = " ".join([token.text for token in token_list])
    
    # Build merged node
    for token in token_list:
        if token in entity_dict.keys():
            assert entity_dict[token].type == "entity", "Type error: " + token.text + str(entity_dict[token].type)
            merged_node.attrs = merge_attr_dicts(merged_node.attrs, entity_dict[token].attrs)
            # entity_dict.pop(token, "Error removing " + token.text)
    
    # Remap entries to merged node
    for token in token_list:
        entity_dict[token] = merged_node
    return entity_dict

def build_entity_dict(doc):
    entity_dict = dict()

    entities = []
    for token in doc:
        if token.pos_ in ["NOUN", "PRON", "PROPN"]:
            entities.append(token)

    for token in entities:
        new_node = Entity(token)
        for child in token.children:
            if child.dep_ == "det":
                new_node.attrs["det"].add(child.text)
            if child.dep_ in ["advcl", "amod"]:
                adj = " ".join([tok.text for tok in child.subtree])
                new_node.attrs["adj"].add(adj)
                
        entity_dict[token] = new_node

    # Combine compound tokens
    print("Merging compounds")
    
    # Method assumes that child compounds always precede parents in Doc
    start_idx, end_idx = None, None
    for i, token in enumerate(doc):
        # Find continuous  compounds
        if token.dep_ == 'compound':
            if not start_idx:
                start_idx = i
        else:
            if start_idx != None:
                end_idx = i + 1
                compound = doc[start_idx:end_idx]
                start_idx, end_idx = None, None
                entity_dict = merge_nodes(compound, entity_dict)
    
    return entity_dict

def build_action_dict(doc):
    nodes = dict()
    actions = []
    for token in doc:
        if token.pos_ in ["VERB"]:
            actions.append(token)
    for token in actions:
        new_node = Action(token)
        # new_node.attrs["type"].append('action')
        for child in token.children:
            if child.dep_ == "det":
                new_node.attrs["det"].add(child.text)
            if child.dep_ in ["advcl", "amod", "advmod"]:
                adj = " ".join([tok.text for tok in child.subtree])
                new_node.attrs["adjectives"].add(adj)
        
        nodes[token] = new_node
    return nodes

def build_adj_dict(doc):
    nodes = dict()
    adjectives = []
    for token in doc:
        if token.pos_ in ["ADV", "ADJ"]:
            adjectives.append(token)
    for token in adjectives:
        new_node = Node(token, token.text, "action")
        # new_node.attrs["type"].append('action')
        # for child in token.children:
        #     if child.dep_ == "det":
        #         new_node.attrs["det"].add(child.text)
        #     if child.dep_ in ["advcl", "advmod"]:
        #         adj = " ".join([tok.text for tok in child.subtree])
        #         new_node.attrs["adj"].add(adj)
        
        nodes[token] = new_node
    return nodes


def get_relations_from_action(action, node_relations, nodes, source=None):
        dest, new_relation = None, None
        for child in action.children:
            if child.dep_ == "nsubj" and not source:
                source = child
            if child.dep_ == "agent" and not source:
                for grandchild in child.children:
                    if grandchild.dep_ == 'pobj':
                        source = grandchild
                        break
            if child.dep_ in ["dobj", "nsubjpass"] :
                dest = child
            if source and source not in nodes.keys():
                print("Weird subject:", source.text)
                
                source = dest
            if dest and dest not in nodes.keys():
                print("Weird object:", dest.text)
                dest = source
        if source:
#             print("relation: ", action.text, nodes[source], nodes[dest])
            if source not in nodes.keys():
                print("Node {} not found".format(source.text))
                nodes[source] = Entity(source)
            
            new_relation = Edge(action.text, nodes[source], nodes[source], action.i * 3600) # Each position equivalent to an hour
            # new_relation = Involved(action.text, nodes[source], nodes[source], action.i * 3600) # Each position equivalent to an hour
            
            if dest:
                new_relation.dest = nodes[dest]
            
            for child in action.children:
#                 if child.dep_ == "det":
#                     new_relation.attrs["det"].append(child.text)
                if child.dep_ in ["advcl", "amod", "advmod"]:
                    adj = " ".join([tok.text for tok in child.subtree])
                    new_relation.attrs["adjectives"].add(adj)
                
                if child.dep_ in ["prep", "xcomp"]:
                    adj = " ".join([tok.text for tok in child.subtree])
                    new_relation.attrs["prepositional_modifier"].add(adj)
                    for grandchild in child.children:
                        if grandchild.dep_ in ["pobj", "dobj"]:
                            if grandchild not in nodes.keys():
                                print("Node {} not found".format(grandchild.text))
                                nodes[grandchild] = Entity(grandchild)
                            if not dest:
                                new_relation.dest = nodes[grandchild]
                            break
                # Pass these trees to the subject
                if child.dep_ in ["acomp"]:
                    subtree = " ".join([tok.text for tok in child.subtree])
                    nodes[source].attrs["adjectival_compliment"].add(subtree)
                
#                 # If 
                if child.dep_ in ["conj"]:
                    get_relations_from_action(child, node_relations, nodes, source=source)
                
                # If destination is still empty, create self-loop
                if not dest:
                    dest = source
                
                # Make sure that dest exists
                if dest not in nodes.keys():
                    nodes[dest] = Entity(dest)
                    print("Node {} not found".format(dest.text))

        if new_relation:
            node_relations.append(new_relation)
#         else:
#             print("Source-less action:", action.text)

def get_sentence_order_relations(doc):
    sentence_order = set()
    prev = None
    for sent in doc.sents:
        for token in sent:
            if token.dep_ == 'ROOT':
#                 print("root at", token.text)
                if prev is not None:
                    sentence_order.add(('Temporal Relation', prev, token))
                prev = token
                break
    return sentence_order



# Workaround for unserializable_results 
# nlp.add_pipe(remove_unserializable_results, last=True)
def remove_unserializable_results(doc):
    doc.user_data = {}
    for x in dir(doc._):
        if x in ['get', 'set', 'has']: continue
        setattr(doc._, x, None)
    for token in doc:
        for x in dir(token._):
            if x in ['get', 'set', 'has']: continue
            setattr(token._, x, None)
    return doc


def resolve_coreferences(doc, nodes, node_relations, verbose=True):
    references = dict()
    cluster_list = doc._.coref_clusters
    for cluster in cluster_list:
        cluster_tokens = []
        for span in cluster.mentions:
            for token in span:
                if token in nodes.keys():
                    cluster_tokens.append(token)
    
        # Note that cluster.main is a span not a token
        references[cluster.main] = cluster_tokens
    if verbose:    
        print("\nCoref:\n", references)
    # Approach 1: Add parent node for coreferences
    # for name, tokens in references.items():
    #     if len(tokens) == 0:
    #         continue
    #     nodes[name.text] = Entity(tokens[0])
    #     for token in tokens:
    #         node_relations.add(Edge("coreference", nodes[name.text], nodes[token], 0))
            
    # Approach 2: Just add property
    for name, _tokens in references.items():
        for token in _tokens:
            nodes[token].attrs["coreferent"] = set([name.text])
    
    # Approach 3: , transfer relations over to first mention
#     for name, tokens in references.items():
#         if len(tokens) == 0:
#             continue
#         first_mention = tokens[0]
#         for token in tokens:
#             if token in nodes.keys():
#                 first_mention = token
#                 break
#         print(first_mention)
#         nodes[first_mention].text = name.text
#         print("Processing", name.text)
#         nodeset = [nodes[token] for token in tokens]
#         for relation in node_relations:
#             if relation.source in nodeset:
#                 print("Found relation", relation.label)
#                 relation.source = nodes[first_mention]
#             if relation.dest in nodeset:
#                 print("Found relation", relation.label)
#                 relation.dest = nodes[first_mention]
    return set(node_relations)


# Recursively builds and trims relations from dependency parse of
# doc, building a parse tree that only including target_tokens
def contract_relations(doc, node_dict):
    # Recursively collapse syntax tree
    tokens = set()
    relation_dict = defaultdict(lambda : set())
    for token in doc:
        tokens.add(token)
        for child in token.children:
            relation_dict[token].add((child.dep_, token, child))

    target_tokens = set(node_dict.keys())
    
    # for source, relations in relation_dict.items():
    #     if source not in target_tokens:
    #         print(source.text, "Needs upwards merging")
    #     else:
    #         for label, src, dest in relations:
    #             if dest not in target_tokens:
                    
    #                 relation_dict[src].add()


    while len(tokens) > len(target_tokens):
        edges_contracted = 0
        # found_invalid_token = False
        # Iterate through all actions and entities
        edges_to_remove, edges_to_add = set(), set()
        
        # For all tokens
        for token in tokens:
            # print(len(edges_to_remove), len(edges_to_add))
            # print("At token", token)
            # Check children
            for label, _, child in relation_dict[token]:
                # Drop any unwanted child nodes, and extend relations to grandchildren
                if child not in target_tokens:
                    # print("Found unwanted child", child)
                    edges_contracted += 1
                    # print("Trimming edge that ends at", child.text)
                    # print("adding to remove", (child.dep_, token, child))
                    if (child.dep_, token, child) in edges_to_remove:
                            print("Duplicate on ", (child.dep_, token, child))
                    else:
                        print("queueing for remove", (child.dep_, token, child))
                    edges_to_remove.add((child.dep_, token, child))
                    for label, _, grandchild in relation_dict[child]:
                    # for grandchild in child.children:
                        # print("Trimming edge that ends at", grandchild.text)
                        edges_contracted += 1
                        edges_to_remove.add((label, child, grandchild))
                        # print("adding to remove", (grandchild.dep_, child, grandchild))
                        if (grandchild.dep_, child, grandchild) in edges_to_remove:
                            print("Duplicate on ", (grandchild.dep_, child, grandchild))
                        label = grandchild.dep_
                        if child.dep_ == "prep":
                            # label = child.text
                            edges_to_add.add((label, token, grandchild))
                            print("Found prep between", token, grandchild)
                            # For prepositions, handle directly
                            print("Breaking out of two loops")
                            break
                        # edges_to_remove.add((label, child, grandchild))
                        edges_to_add.add((label, token, grandchild))
                    # This is to handle a double break. If the for loop terminates normally, it runs this branch and continues to next iteration
                    else:
                        continue
                    break
            else:
                continue
            break
        # print(relation_dict)
        for label, source, dest in edges_to_remove:
            # print("Removing", label, source, dest)
            relation_dict[source].remove((label, source, dest))
        
        for label, source, dest in edges_to_add:
            # print("adding", (label, source, dest))
            relation_dict[source].add((label, source, dest))

        # print("Trimmed", edges_contracted, "nodes. Second check", len(edges_to_remove))

        # If nothing is trimmed, then tree can no longer be trimmed
        if edges_contracted == 0:
            break
    # print(len(tokens), len(target_tokens))
    # print(tokens)
    # print(target_tokens)
    relation_tups = set()
    for key, relations in relation_dict.items():
        if len(relations) > 0 and key in target_tokens:
            relation_tups.update(relations)
        else:
            # print("Invalid tups:", [rel for rel in relations])
            pass
    # print(relation_tups)
    
    return relation_tups

"""
Outline:
1. Setup spacy model
2. Preprocess text, then feed into spacy
3. Get tokens for actions & entities
4. Build token-based parse tree, adding all relations
5. Build nodes from tokens
6. Get relations from parse trees
7. Add temporal ordering between actions
8. Map entity tokens to coreference clusters
9. Build parallel story graph contracted along coreferences
"""
def parse_soup(text, raw=False, verbose=True,title="default", model="en_core_web_sm"):
    # 1. Setup spacy model
    print("Setting up spacy model")
    nlp = spacy.load(model)
    neuralcoref.add_to_pipe(nlp)

    
    # Preprocess text, then feed into spacy
    print("Processing Text")
    text = text.strip()
    print("Text:\n", text)
    doc = nlp(text)
#     displacy.render(doc, style='dep', jupyter=True)
     

    # 5. Build nodes from tokens
    print("Build nodes from parse trees")
    token_nodes = dict()
    if raw:
        for token in doc:
            node = Node(token, token.text, "raw")
            node.attrs['pos'] = set([token.pos_])
            token_nodes[token] = node
        node_dict = token_nodes
    else:
        node_dict = build_entity_dict(doc)
        
        # Add actions as nodes too
        action_dict = build_action_dict(doc)
        node_dict.update(action_dict)

    if verbose:
        print("Nodes:")
        nodes = set([node for _, node in node_dict.items()])
        for node in nodes:
            print("\t", node.text, dict(node.attrs))

    # 6. Get relations between nodes
    node_relations = set()
    if raw:
        print("Building complete syntactic parse tree")
        for token in doc:
            for child in token.children:
                node_relations.add(Edge(child.dep_, node_dict[token], node_dict[child]))
    else:
        relation_tups = contract_relations(doc, node_dict)
        print(relation_tups)
        node_relations = set([Involved(node_dict[src], node_dict[dest]) for label, src, dest in relation_tups])


    # Use actions as relations
    # for action in actions:
    #     get_relations_from_action(action, node_relations, node_dict)
    
    
    
    # 7. Add temporal ordering between actions
#     print("Getting temporal ordering between actions")
#     temporal_relations = get_sentence_order_relations(doc)
    
    # 8. Map entity tokens to coreference clusters
    print("Resolving entity coreferences")    
    node_relations = resolve_coreferences(doc, node_dict, node_relations, verbose=verbose)

#     print("\nEnts: ", doc.ents)
    
    # For now, return all nodes
    if verbose:
        print("Relations:")
        for relation in node_relations:
            print(relation, dict(relation.attrs))
    
    graph = StoryGraph(title=title)
    
    graph.node_dict = node_dict
    graph.read_node_dict()
    # graph.nodes = set([node for _, node in node_dict.items()])
    graph.edges = set(node_relations)
    # return [node for key, node in nodes.items()], node_relations , doc
    return graph, doc



DATA_PATH = "data/"
def read_txt(filename):
    f = open(DATA_PATH + filename, "r")
    contents = f.read()
    f.close()
    return contents

iron_man = read_txt("ironman1.txt")

summary = read_txt("anaconda.txt")
simple_summary = """A poacher hides from an unknown creature in his boat. It breaks through the boat and attempts to catch the poacher."""
medium_summary = read_txt("anaconda_md.txt")
anaconda_sents = medium_summary.split(".")
wasp_sentence = anaconda_sents[4]

tortoise_hare = """The story concerns a Hare who ridicules a slow-moving Tortoise. Tired of the Hare's arrogant behaviour, the Tortoise challenges him to a race. The hare soon leaves the tortoise behind. Confident of winning, the Hare takes a nap midway through the race. When the Hare awakes however, he finds that his competitor, crawling slowly but steadily, has arrived before him. """
short_tortoise = "The story concerns a Hare who ridicules a slow-moving Tortoise."
hare_sents = tortoise_hare.split(".")

if __name__ == '__main__':
    # spacy.load('en_core_web_lg')
    # nodes, relations, doc = parse_soup(iron_man.split('.')[0], raw=True, verbose=True)
    graph, doc = parse_soup(iron_man.split('.')[1], raw=False, verbose=False, title="ironman2", model="en_core_web_sm")
    # entities, actions, relations, doc = parse_soup(simple_summary)
    # graph = render_story_graph(nodes, relations, graph_name="simplesummary")
    graph.visualize()
    graph.write_graph_ml()

    # nxGraph = pyviz_to_nx(graph)
    # write_graphml(nxGraph, "test.xml")