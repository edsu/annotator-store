from datetime import datetime
import iso8601

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
                    'startOffset': {'type': 'long', 'index': 'no'},
                    'endContainer': {'type': 'string', 'index': 'no'},
                    'endOffset': {'type': 'long', 'index': 'no'},

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
                    'start': {'type': 'long'},
                    'end':   {'type': 'long'},
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
    'references': {'type': 'string', 'index': 'not_analyzed'}
}


class Annotation(es.Model):

    __type__ = TYPE
    __mapping__ = MAPPING

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
