"""
infrastructure/search/client.py

Singleton Elasticsearch client factory.
"""

from __future__ import annotations

from elasticsearch import Elasticsearch

_client: Elasticsearch | None = None


def get_es_client() -> Elasticsearch:
    global _client
    if _client is None:
        from django.conf import settings
        _client = Elasticsearch(settings.ELASTICSEARCH_URL)
    return _client
