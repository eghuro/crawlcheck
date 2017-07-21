# Crawlcheck

Crawlcheck is a web crawler invoking plugins on received content.
It's intended for verification of websites prior to deployment.
The process of verification is customizable by configuration script that allows
complex specification which plugins should check particular URIs and
content-types.

## Version

1.0.0

## Dependencies

Crawlcheck's engine currently runs on Python 3.5 and uses SQLite3 as a
database backend. Crawlcheck uses a number of open source projects to work
properly. Python dependencies are listed in
[requirements.txt](https://github.com/eghuro/crawlcheck/blob/master/requirements.txt)

For a web report, there's a [separate project](https://github.com/eghuro/crawlcheck-report).

## Installation

0) You will need python3, python-pip and sqlite3, virtualenv, libmagic, libtidy,
libxml2 and libxslt installed. All dev or devel versions.

1) Fetch sources

```sh
git clone https://github.com/eghuro/crawlcheck crawlcheck
```

2) Run install script

```sh
cd crawlcheck
pip install -r requirements.txt
```

## Configuration

A configuration file is a YAML file defined as follows:

```sh
---
version: 1.05                   # configuration format version
database: crawlcheck.sqlite     # SQLite database file
maxDepth: 10                    # max amount of links followed from any entry point (default: 0 meaning unlimited)
agent: "Crawlcheck/1.05"        # user agent used (default: Crawlcheck/1.05)
logfile: cc.log                 # where to store logs
maxContentLength: 2000000       # max file size to download
pluginDir: plugin               # where to look for plugins (including subfolders, default: 'plugin')
timeout: 1                      # timeout for networking (default: 1)
cleandb: True                   # clean the database before execution
initdb: True                    # initialize the database
report: "http://localhost:5000" # report REST API
cleanreport: True               # clean entries in the report before sending current
maxVolume: 100000000            # max 100 MB of temp files (default: sys.maxsize)
maxAttempts: 2                  # attempts to download a web page (default: 3)
dbCacheLimit: 1000000           # cache up to 1M of DB queries
tmpPrefix: "Crawlcheck"         # prefix for temporary file names with downloaded content (default: Crawlcheck)
tmpSuffix: "content"            # suffix for temporary file names with downloaded content (default: content)
tmpDir: "/tmp/"                 # where to store temporary files (default: /tmp/)
dbCacheLimit: 100000            # the amount of cached database queries (default: sys.maxsize)
urlLimit: 10000000              # limit on seen URIs
verifyHttps: True               # verify HTTPS? (default: False)
cores: 2                        # the amount of cores available (eg. for parallel report payload generation)
recordParams: False             # record request data or URL params? (default: True)
recordHeaders: False            # record response headers? (default: True)
sitemap-file: "sitemap.xml"     # where to store generated sitemap.xml
sitemap-regex: "https?://ksp.mff.cuni.cz(/.*)?" # regex for sitemap generator
yaml-out-file: "cc.yml"         # where to write YAML report
report-file: "report"           # where to write PDF report (.pdf will be added automatically)

# other parameters used by plugins written as ```key: value```

content-types:
 -
    "content-type": "text/html"
    plugins: # plugins to use for given content-type
       - linksFinder
       - tidyHtmlValidator
       - css_scraper
       - formChecker
       - seoimg
       - seometa
       - dupdetect
       - non_semantic_html
 -
    "content-type": "text/css"
    plugins:
       - tinycss
       - dupdetect
 -
    "content-type": "application/gzip"
    plugins:
       - sitemapScanner
-
    "content-type": "application/xml"
    plugins:
       - sitemapScanner
       - dupdetect

urls:
 -
    url: "http://mj.ucw.cz/vyuka/.+"
    plugins: # which plugins are allowed for given URL
       - linksFinder
       - tidyHtmlValidator
       - tinycss
       - css_scraper
       - formChecker
       - seoimg
       - seometa
       - dupdeteict
       - non_semantic_html
 -
    url: "http://mj.ucw.cz/" #test links (HEAD request) only
    plugins:

filters: #Filters (plugins of category header and filter) that can be used
 - depth
 - robots
 - contentLength
 - canonical
 - acceptedType
 - acceptedUri
 - uri_normalizer
 - expectedType

postprocess:
 - sitemap_generator
 - report_exporter
 - yaml_exporter
 - TexReporter

entryPoints: # where to start
# Note, that once URI get's to the database it's no longer being requested
# (beware of repeated starts, if entry point remains in the database execution won't
# start from this entry point)
 - "http://mj.ucw.cz/vyuka/"
```

## Running crawlcheck

Assuming you have gone through set-up and configuration, now run checker:

```sh
cd [root]/crawlcheck/src/
python checker/ [config.yml]
```

Note: ``[root]/crawlcheck`` is where repository was cloned to,
``[config.yml]`` stands for the configuration file path.

## Plugins

There are currently 5 types of plugins: crawlers, checkers, headers, filters,
and postprocessors. The crawlers are specializing in discovering new links.
The checkers check the syntax of various files. The headers check HTTP headers
and together with the filters serve to customize the crawling process itself.
The postprocessors are used to generate reports or other outputs from
the application.

Crawlcheck is currently extended with the following plugins:

* linksFinder (crawler)
* sitemapScanner (crawler)
* tidyHtmlValidator (checker)
* tinycss (checker)
* css_scraper (checker)
* seoimg (checker)
* seometa (checker)
* dupdetect (checker)
* non_semantic_html (checker)
* contentLength (header)
* expectedType (header)
* canonical (header)
* acceptedType (header)
* acceptedUri (header)
* uri_normalizer (header)
* depth (filter)
* robots (filter)
* report_exporter (postprocessor)
* yaml_exporter (postprocessor)
* sitemap_generator (postprocessor)
* TexReporter (postprocessor)

## How to write a plugin

Go to ``crawlcheck/src/checker/plugin/``, create ``my_new_plugin.py`` and
``my_new_plugin.yapsy-plugin`` files there.
Fill out the .yapsy-plugin file:

```sh
[Core]
Name = Human readable plugin name
Module = my_new_plugin

[Documentation]
Author = Your Name
Version = 0.0
Description = My New Plugin
```

For plugin itself you need to implement following:

```sh
from yapsy.IPlugin import IPlugin
from common import PluginType
from filter import FilterException  # for headers and filters
class MyPlugin(IPlugin):

    category = PluginType.CHECKER # pick appropriate type
    id = myPlugin

    def setJournal(self, journal):
        # record journal somewhere - all categories

    def setQueue(self, queue):
        # record queue somewhere - if needed

    def setConf(self, conf):
        # record configuration - only headers and filters

    def check(self, transaction):
        # implement the checking logic here for crawlers and checkers

    def filter(self, transaction):
        # implement the filtering logic here for filters and headers
        # raise FilterException to filter the transaction out

    def setDb(self, db):
        # record DB somewhere - only postprocessors

    def process(self):
        # implement the postprocessing logic here for postprocessor
```

See <http://yapsy.sourceforge.net/IPlugin.html> and
<http://yapsy.sourceforge.net/PluginManager.html#plugin-info-file-format> for
more details.

## License

MIT
