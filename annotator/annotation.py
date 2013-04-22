from annotator import es, authz
from flask import current_app, g

TYPE = 'annotation'
MAPPING = {
    'annotator_schema_version': {'type': 'string'},
    'created': {'type': 'date'},
    'updated': {'type': 'date'},
    'quote': {'type': 'string'},
    'tags': {'type': 'string', 'index_name': 'tag'},
    'text': {'type': 'string'},
    'deleted': {'type': 'boolean'},
    'uri': {'type': 'string', 'index': 'not_analyzed'},
    'user': {'type': 'string', 'index': 'not_analyzed'},
    'consumer': {'type': 'string', 'index': 'not_analyzed'},

    'target': {
        'properties': {
            'id': {
                'type': 'multi_field',
                'path': 'just_name',
                'fields': {
                    'id': {'type': 'string', 'index': 'not_analyzed'},
                    'uri': {'type': 'string', 'index': 'not_analyzed'},
                },
            },
            'source': {
                'type': 'multi_field',
                'path': 'just_name',
                'fields': {
                    'source': {'type': 'string', 'index': 'not_analyzed'},
                    'uri': {'type': 'string', 'index': 'not_analyzed'},
                },
            },
            'selector': {
                'properties': {
                    'type': {'type': 'string', 'index': 'no'},

                    # Annotator XPath+offset selector
                    'startContainer': {'type': 'string', 'index': 'no'},
                    'startOffset': {'type': 'string', 'index': 'no'},
                    'endContainer': {'type': 'string', 'index': 'no'},
                    'endOffset': {'type': 'string', 'index': 'no'},

                    # Open Annotation TextQuoteSelector
                    'exact': {
                        'type': 'multi_field',
                        'path': 'just_name',
                        'fields': {
                            'exact': {'type': 'string'},
                            'quote': {'type': 'string'},
                        },
                    },
                    'prefix': {'type': 'string'},
                    'suffix': {'type': 'string'},

                    # Open Annotation (Data|Text)PositionSelector
                    'start': {'type': 'integer'},
                    'end':   {'type': 'integer'},
                }
            }
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
    },
    'document': {
        'properties': {
            'title': {'type': 'string'},
            'link': {
                'type': 'nested',
                'properties': {
                    'type': {'type': 'string', 'index': 'not_analyzed'},
                    'href': {'type': 'string', 'index': 'not_analyzed'},
                }
            }
        }
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
    def locate(cls, uri, offset=0, limit=20):
        q = cls._builds_query(offset, limit)
        print q

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
        _add_default_permissions(self)
        super(Annotation, self).save(*args, **kwargs)


def _add_default_permissions(ann):
    if 'permissions' not in ann:
        ann['permissions'] = {'read': [authz.GROUP_CONSUMER]}
