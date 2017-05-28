from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext


__version__ = '0.1.0'

# TODO: If you need to log, use loggers named after the current Python module
logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Raspiradio'
    ext_name = 'raspiradio'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['refresh_rate'] = config.Integer()
        schema['artist_font_file'] = config.Path()
        schema['artist_font_size'] = config.Integer()
        schema['album_font_file'] = config.Path()
        schema['album_font_size'] = config.Integer()
        schema['title_font_file'] = config.Path()
        schema['title_font_size'] = config.Integer()
        schema['progress_bar_font_file'] = config.Path()
        schema['progress_bar_font_size'] = config.Integer()
        schema['lcd_config'] = config.String()
        return schema

    def setup(self, registry):
        # You will typically only implement one of the following things
        # in a single extension.

        # TODO: Edit or remove entirely
        from .raspiradio_frontend import RaspiradioFrontend
        registry.add('frontend', RaspiradioFrontend)

        # TODO: Edit or remove entirely
        #from .backend import FoobarBackend
        #registry.add('backend', FoobarBackend)

        ## TODO: Edit or remove entirely
        #registry.add('http:static', {
        #    'name': self.ext_name,
        #    'path': os.path.join(os.path.dirname(__file__), 'static'),
        #})
