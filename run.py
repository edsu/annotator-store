import os
import logging

import annotator

def _configure_logger(app):
    admins = app.config.get('ADMINS')

    if admins and not app.debug:
        handler = logging.handlers.SMTPHandler('127.0.0.1',
                                               'server-error@no-reply.com',
                                               admins,
                                               'Annotator error')
        handler.setLevel(logging.ERROR)
        app.logger.addHandler(handler)

if __name__ == '__main__':
    annotator.create_app()
    annotator.app.run()
