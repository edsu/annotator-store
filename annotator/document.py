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
    def get_by_uri(cls, uri):
        """returns the first document match for a given URL"""
        results = cls.get_all_by_uris([uri])
        return results[0] if len(results) > 0 else []

    @classmethod
    def get_all_by_uris(cls, uris):
        """returns a list of documents that have any of the supplied uris
        It is only necessary for one of the supplied uris to match.
        """
        q = {
            "query": {
                "nested": {
                    "path": "link", 
                    "query": {
                        "terms": {
                            "link.href": uris
                        }
                    }
                }
            },
            "sort": [
              {
                "updated": {
                  "order": "asc"
                }
              }
            ]
        }
        res = cls.es.conn.search_raw(q, cls.es.index, cls.__type__)
        return [cls(d['_source'], id=d['_id']) for d in res['hits']['hits']]

    def uris(self):
        """Returns a list of the uris for the document"""
        return self._uris_from_links(self.get('link', []))

    def merge_links(self, links):
        current_uris = self.uris()
        for l in links:
            if l['href'] and l['type'] and l['href'] not in current_uris:
                self['link'].append(l)

    def _uris_from_links(self, links):
        uris = []
        for link in links:
            uris.append(link.get('href'))
        return uris


