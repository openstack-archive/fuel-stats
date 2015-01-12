from collections import defaultdict
import csv
from migration.config import DOC_TYPE_ACTION_LOGS
import os
from elasticsearch import Elasticsearch
from structure_skeleton import STRUCTURE_SKELETON


ELASTIC_HOST = 'product-stats.mirantis.com'
ELASTIC_PORT = 443
ELASTIC_USE_SSL = True

# ELASTIC_HOST = 'localhost'
# ELASTIC_PORT = 9200
# ELASTIC_USE_SSL = False

INDEX_FUEL = 'fuel'
DOC_TYPE_STRUCTURE = 'structure'

es = Elasticsearch(hosts=[
    {'host': ELASTIC_HOST,
     'port': ELASTIC_PORT,
     'use_ssl': ELASTIC_USE_SSL}
])


def query_structure(query):
    return es.search(index=INDEX_FUEL, doc_type=DOC_TYPE_STRUCTURE, body=query)


def get_data(query, doc_type=None, show_fields=None, chunk_size=10000):
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
        response = es.search(index=INDEX_FUEL, doc_type=doc_type, body=paged_query)
        total = response["hits"]["total"]
        received += chunk_size
        paged_query["from"] = received
        result.extend([d["_source"] for d in response["hits"]["hits"]])
        if total <= received:
            break
    return result


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
            for val in (nodes_manufacturers + [None] * (3 - len(nodes_manufacturers)))[0:3]:
                flatten_clusters[idx].append(val)
            nodes_platform_name = extract_platform_name(cluster.get('nodes', []))
            flatten_clusters[idx].append(len(nodes_platform_name) >= 3)
            for val in (nodes_platform_name + [None] * (3 - len(nodes_platform_name)))[0:3]:
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


def inst_info_idx(structure_key_paths, flatten_structures):
    struct_mn_uid_idx = structure_key_paths.index(['master_node_uid'])
    fs_idx = {}
    for ii in flatten_structures:
        mn_uid = ii[struct_mn_uid_idx]
        fs_idx[mn_uid] = ii
    return fs_idx


def get_segmentation_type(deployment_info):
    return deployment_info.get('quantum_settings', {}).get('L2', {}).get(
        'segmentation_type')


def get_deployment_al_idx(action_logs):
    result = defaultdict(dict)
    for al_data in action_logs:
        d_infos = get_deployment_info(al_data)
        for d_info in d_infos:
            seg_type = get_segmentation_type(d_info)
            if seg_type:
                mn_uid = al_data['master_node_uid']
                cluster_id = al_data['cluster_id']
                if cluster_id not in result[mn_uid]:
                    result[mn_uid][cluster_id] = {}
                result[mn_uid][cluster_id]['segmentation_type'] = seg_type
    return result


def get_deployment_info(al_data):
    return al_data['additional_info'].get('output', {}).get(
        'args', {}).get('deployment_info', [])


def main():
    structures_query = {
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
    structures = get_data(structures_query, doc_type=DOC_TYPE_STRUCTURE)

    CLUSTER_SKELETON = STRUCTURE_SKELETON.pop('clusters')[0]
    CLUSTER_SKELETON.pop('nodes')
    CLUSTER_SKELETON.pop('node_groups')

    # export of installations info
    structure_key_paths = get_keys_paths([], STRUCTURE_SKELETON)
    flatten_structures = get_flatten_structure(structure_key_paths, structures)
    fs_idx = inst_info_idx(structure_key_paths, flatten_structures)
    # inst_file = os.path.join(os.path.dirname(__file__), 'installations.csv')
    # export_to_csv(inst_file, structure_key_paths, flatten_structures)
    # print "### installations info exported to CSV"
    #
    clusters_key_paths = get_keys_paths([], CLUSTER_SKELETON)
    clusters_key_paths, flatten_clusters = get_flatten_clusters(clusters_key_paths, structures)
    # clusters_file = os.path.join(os.path.dirname(__file__), 'clusters.csv')
    # export_to_csv(clusters_file, clusters_key_paths, flatten_clusters)
    # print "### clusters info exported to CSV"

    # action_logs_query = {
    #     "query": {
    #         "filtered": {
    #             "filter": {
    #                 "and": [
    #                     {"range": {"start_timestamp": {"gt": "now-1M"}}},
    #                     # {"term": {"master_node_uid": "780acfbf-3412-4eb0-a61e-eccbff952eb4"}},
    #                     {"term": {"action_name": "deployment"}}
    #                 ]
    #             }
    #         }
    #     }
    # }
    # action_logs = get_data(action_logs_query, doc_type=DOC_TYPE_ACTION_LOGS)
    # deployment_al_idx = get_deployment_al_idx(action_logs)
    # for d_al in deployment_al_idx:
    #     print "### deployment_al_idx", d_al

    flatten_key_paths = clusters_key_paths + structure_key_paths
    flatten_info = []
    cluster_mn_uid_idx = clusters_key_paths.index(['master_node_uid'])
    # cluster_id_idx = clusters_key_paths.index(['id'])
    for ci in flatten_clusters:
        mn_uid = ci[cluster_mn_uid_idx]
        # seg_type = deployment_al_idx.get(mn_uid, {}).get(ci[cluster_id_idx], {}).get('segmentation_type')
        flatten_info.append(ci + fs_idx[mn_uid])
    flatten_file = os.path.join(os.path.dirname(__file__), 'flatten.csv')
    export_to_csv(flatten_file, flatten_key_paths, flatten_info)
    print "### flatten info exported to CSV"


if __name__ == '__main__':
    main()