from annotator import es

TYPE = 'document'
MAPPING = {
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'link': {
        'type': 'nested',
        'properties': {
            'type': {'type': 'string', 'index': 'not_analyzed'},
            'href': {'type': 'string', 'index': 'not_analyzed'},
        }
    },
    'title': {'type': 'string'}
}

class Document(es.Model):
    __type__ = TYPE
    __mapping__ = MAPPING

    @classmethod
    def get_by_url(cls, url):
        results = cls.get_all_by_url(url)
        return results[0] if len(results) > 0 else []

    @classmethod
    def get_all_by_url(cls, url):
        q = {"nested": {"path": "link", "query": {"term": {"link.href": url}}}}
        res = cls.es.conn.search(q, cls.es.index, cls.__type__, sort=sort)
        return [cls(d) for d in res]
