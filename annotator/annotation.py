from datetime import datetime
import iso8601

from annotator import es, authz
from flask import current_app, g

TYPE = 'annotation'
MAPPING = {
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'tags': {'type': 'string', 'index_name': 'tag'},
    'text': {'type': 'string'},
    'uri': {'type': 'string', 'index': 'not_analyzed'},
    'user' : {'type': 'string', 'index' : 'not_analyzed'},
    'consumer': {'type': 'string', 'index': 'not_analyzed'},
    'target': {
        'index_name': 'not_analyzed',
        'properties': {
            'id': {'type': 'string', 'index': 'not_analyzed'},
            'selector': {
                'index_name': 'not_analyzed',
                'properties': {
                    'source': {'type': 'string', 'index': 'not_analyzed'},

                    # supported values for type: 'xpath range', 'context+quote', 'position'
                    'type': {'type': 'string', 'index_name': 'selector_type'},

                    # parameters for 'xpath range' -type selectors
                    'startXpath': {'type': 'string', 'index': 'not_analyzed'},
                    'endXpath':   {'type': 'string', 'index': 'not_analyzed'},
                    'startOffset': {'type': 'integer'},
                    'endOffset':   {'type': 'integer'},

                    # parameters for 'context+quote' -type selectors
                    'exact': {'type': 'string', 'index': 'not_analyzed'},
                    'prefix': {'type': 'string', 'index': 'not_analyzed'},
                    'suffix': {'type': 'string', 'index': 'not_analyzed'},

                    # parameters for 'position' -type selectors
                    'start': {'type': 'integer', 'index_name': 'not_analyzed'},
                    'end': {'type': 'integer', 'index_name': 'not_analyzed'},

                }
            }
        }
    },  
    'ranges': {    #ranges is not used anymore, but annotations created earlier will have it, so we need to read it
        'index_name': 'range',
        'properties': {
            'start': {'type': 'string', 'index': 'not_analyzed'},
            'end':   {'type': 'string', 'index': 'not_analyzed'},
            'startOffset': {'type': 'integer'},
            'endOffset':   {'type': 'integer'},
        }
    },
    'permissions': {
        'index_name': 'permission',
        'properties': {
            'read':   {'type': 'string', 'index': 'not_analyzed'},
            'update': {'type': 'string', 'index': 'not_analyzed'},
            'delete': {'type': 'string', 'index': 'not_analyzed'},
            'admin':  {'type': 'string', 'index': 'not_analyzed'}
        }
    },
    'thread': {
        'type': 'string',
        'analyzer': 'thread'
    }
}
SETTINGS = {
    'analysis': {
        'analyzer': {
            'thread': {
                'tokenizer': 'path_hierarchy'
            }
        }
    }
}

class Annotation(es.Model):

    __type__ = TYPE
    __mapping__ = MAPPING
    __settings__ = SETTINGS

    @classmethod
    def _build_query(cls, offset=0, limit=20, **kwargs):
        q = super(Annotation, cls)._build_query(offset, limit, **kwargs)

        if current_app.config.get('AUTHZ_ON'):
            f = authz.permissions_filter(g.user)
            if not f:
                return False # Refuse to perform the query
            q['query'] = {'filtered': {'query': q['query'], 'filter': f}}

        return q

    @classmethod
    def _build_query_raw(cls, request):
        q, p = super(Annotation, cls)._build_query_raw(request)

        if current_app.config.get('AUTHZ_ON'):
            f = authz.permissions_filter(g.user)
            if not f:
                return {'error': "Authorization error!", 'status': 400}, None
            q['query'] = {'filtered': {'query': q['query'], 'filter': f}}

        return q, p

    def save(self, *args, **kwargs):
        # For brand new annotations
        _add_created(self)
        _add_default_permissions(self)

        # For all annotations about to be saved
        _add_updated(self)

        super(Annotation, self).save(*args, **kwargs)


def _add_created(ann):
    if 'created' not in ann:
        ann['created'] = datetime.now(iso8601.iso8601.UTC).isoformat()

def _add_updated(ann):
    ann['updated'] = datetime.now(iso8601.iso8601.UTC).isoformat()

def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}
