import csv
import os
from elasticsearch import Elasticsearch
from structure_skeleton import STRUCTURE_SKELETON


ELASTIC_HOST = 'product-stats.mirantis.com'
ELASTIC_PORT = 443
ELASTIC_USE_SSL = True

INDEX_FUEL = 'fuel'
DOC_TYPE_STRUCTURE = 'structure'

es = Elasticsearch(hosts=[
    {'host': ELASTIC_HOST,
     'port': ELASTIC_PORT,
     'use_ssl': ELASTIC_USE_SSL}
])


def query_structure(query):
    return es.search(index=INDEX_FUEL, doc_type=DOC_TYPE_STRUCTURE, body=query)


def get_structures(query, show_fields=None, chunk_size=100):
    """
    Gets structures from the Elasticsearch by querying by chunk_size
    number of structures
    :param query: Elasticsearch query
    :param show_fields: list of selected fields. All fields will be fetched,
    if show_fields is not set
    :param chunk_size: size of fetched structures chunk
    :return: list of fetched structures
    """
    received = 0
    paged_query = query.copy()
    paged_query["from"] = received
    paged_query["size"] = chunk_size
    if show_fields:
        paged_query["_source"] = show_fields
    result = []
    while True:
        response = es.search(index=INDEX_FUEL, doc_type=DOC_TYPE_STRUCTURE, body=paged_query)
        total = response["hits"]["total"]
        received += chunk_size
        paged_query["from"] = received
        result.extend([d["_source"] for d in response["hits"]["hits"]])
        if total <= received:
            break
    return result


def export_to_csv(file_name, flatten_structures):
    """
    Writes flatten_structures to file_name
    :param file_name: output file name
    :param flatten_structures: list of structures
    :return: None
    """
    with open(file_name, 'wb') as f:
        w = csv.writer(f)
        for structure in flatten_structures:
            w.writerow(structure)


def get_flatten_structure(keys_paths, structures):
    result = []
    for structure in structures:
        flatten_structure = []
        for key_path in keys_paths:
            d = structure
            # print "### key_path", key_path
            for key in key_path:
                # print "### d", d
                d = d.get(key, None)
                if d is None:
                    break
            if isinstance(d, (list, tuple)):
                flatten_structure.append(' '.join(d))
            else:
                flatten_structure.append(d)
            # print "### flatten_structure", flatten_structure
        result.append(flatten_structure)
    return result


def extract_nodes_fields(field, nodes):
    result = set([d.get(field) for d in nodes])
    return filter(lambda x: x is not None, result)


def extract_nodes_manufacturers(nodes):
    return extract_nodes_fields('manufacturer', nodes)


def extract_platform_name(nodes):
    return extract_nodes_fields('platform_name', nodes)


def get_flatten_clusters(keys_paths, structures):
    result = []
    for structure in structures:
        clusters = structure.get('clusters', [])
        flatten_clusters = get_flatten_structure(keys_paths, clusters)
        for idx, cluster in enumerate(clusters):
            flatten_clusters[idx].append(structure['master_node_uid'])
            nodes_manufacturers = extract_nodes_manufacturers(cluster.get('nodes', []))
            flatten_clusters[idx].append(len(nodes_manufacturers) >= 3)
            for val in nodes_manufacturers + [None] * (3 - len(nodes_manufacturers)):
                flatten_clusters[idx].append(val)
            nodes_platform_name = extract_platform_name(cluster.get('nodes', []))
            flatten_clusters[idx].append(len(nodes_platform_name) >= 3)
            for val in nodes_platform_name + [None] * (3 - len(nodes_platform_name)):
                flatten_clusters[idx].append(val)
        result.extend(flatten_clusters)
    return keys_paths + [['master_node_uid'],
                         ['nodes_manufacturers_gt3'],
                         ['nodes_manufacturers_0'], ['nodes_manufacturers_1'], ['nodes_manufacturers_2'],
                         ['nodes_platform_name_gt3'],
                         ['nodes_platform_name_0'], ['nodes_platform_name_1'], ['nodes_platform_name_2']], result


def get_keys_paths(keys, skeleton):
    result = []
    if isinstance(skeleton, dict):
        for k in sorted(skeleton.keys()):
            result.extend(get_keys_paths(keys + [k], skeleton[k]))
    else:
        result.append(keys)
    return result


def export_to_csv(file_name, keys_paths, flatten_structures):
    names = []
    for key_path in keys_paths:
        names.append('.'.join(key_path))
    # print "### names", keys_paths
    # print "### names", names
    with open(file_name, 'wb') as f:
        w = csv.writer(f)
        w.writerow(names)
        for row in flatten_structures:
            w.writerow(row)


def main():
    query = {
        "query": {
            "filtered": {
                "filter": {
                    "or": [
                        {"range": {"modification_date": {"gt": "now-1M"}}},
                        {"range": {"creation_date": {"gt": "now-1M"}}}
                    ]
                }
            }
        }
    }

    structures = get_structures(query)

    CLUSTER_SKELETON = STRUCTURE_SKELETON.pop('clusters')[0]
    CLUSTER_SKELETON.pop('nodes')
    CLUSTER_SKELETON.pop('node_groups')

    # export of installations info
    structure_key_paths = get_keys_paths([], STRUCTURE_SKELETON)
    flatten_structures = get_flatten_structure(structure_key_paths, structures)

    inst_file = os.path.join(os.path.dirname(__file__), 'installations.csv')
    export_to_csv(inst_file, structure_key_paths, flatten_structures)
    print "### installations info exported to CSV"

    clusters_key_paths = get_keys_paths([], CLUSTER_SKELETON)
    # print "### cluster_key_paths", clusters_key_paths
    clusters_key_paths, flatten_clusters = get_flatten_clusters(clusters_key_paths, structures)
    clusters_file = os.path.join(os.path.dirname(__file__), 'clusters.csv')
    export_to_csv(clusters_file, clusters_key_paths, flatten_clusters)
    print "### clusters info exported to CSV"


if __name__ == '__main__':
    main()