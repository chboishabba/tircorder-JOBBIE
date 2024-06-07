# pelicanconf.py
from __future__ import unicode_literals

# Basic settings
AUTHOR = 'Your Name'
SITENAME = 'Audio Recordings Timeline'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'UTC'

DEFAULT_LANG = 'en'

# Theme settings
THEME = 'notmyidea'  # You can change this to any Pelican theme you like

# Plugins
PLUGIN_PATHS = ['pelican-plugins']
PLUGINS = ['']

# Static paths and extra settings
STATIC_PATHS = ['extra']
EXTRA_PATH_METADATA = {
    'extra/custom.css': {'path': 'static/custom.css'},
    'extra/custom.js': {'path': 'static/custom.js'},
}

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True
 
