#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from elasticsearch import Elasticsearch

from fuel_analytics.api.app import app


class EsClient(object):

    def __init__(self):
        self.es = Elasticsearch(hosts=[
            {'host': app.config['ELASTIC_HOST'],
             'port': app.config['ELASTIC_PORT'],
             'use_ssl': app.config['ELASTIC_USE_SSL']}
        ])

    def fetch_all_data(self, query, doc_type, show_fields=(),
                       sort=({"_id": {"order": "asc"}},), chunk_size=100):
        """Gets structures from the Elasticsearch by querying by chunk_size
        number of structures
        :param query: Elasticsearch query
        :param doc_type: requested document type
        :param show_fields: tuple of selected fields.
        All fields will be fetched, if show_fields is not set
        :param sort: tuple of fields for sorting
        :param chunk_size: size of fetched structures chunk
        :return: list of fetched structures
        """
        received = 0
        paged_query = query.copy()
        paged_query["from"] = received
        paged_query["size"] = chunk_size
        if sort:
            paged_query["sort"] = sort
        if show_fields:
            paged_query["_source"] = show_fields
        while True:
            app.logger.debug("Fetching chunk from ElasticSearch. "
                             "From: %d, size: %d",
                             paged_query["from"], chunk_size)
            response = self.es.search(index=app.config['ELASTIC_INDEX_FUEL'],
                                      doc_type=doc_type, body=paged_query)
            total = response["hits"]["total"]
            received += chunk_size
            paged_query["from"] = received
            for d in response["hits"]["hits"]:
                yield d["_source"]
            app.logger.debug("Chunk from ElasticSearch is fetched. "
                             "From: %d, size: %d",
                             paged_query["from"], chunk_size)
            if total <= received:
                break

    def get_structures(self):
        app.logger.debug("Fetching structures info from ElasticSearch")
        query = {"query": {"match_all": {}}}
        doc_type = app.config['ELASTIC_DOC_TYPE_STRUCTURE']
        return self.fetch_all_data(query, doc_type)
