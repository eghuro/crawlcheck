# Crawlcheck

Crawlcheck is a web crawler invoking plugins on received content. It's intended for verification of websites prior to deployment. The process of verification is customisable by configuration script that allows complex specification which plugins should check particular URIs and content-types. Main engine and plugins are written in Python, there's also possibility to show report in form of website written in Ruby on Rails or generate report in PDF. The report contains discoveries plugins made during the verification.

![travis-ci](https://api.travis-ci.org/eghuro/crawlcheck.svg?branch=master) ![codecov](https://img.shields.io/codecov/c/github/eghuro/crawlcheck/master.svg)

### Version
0.04

### Tech

Crawlcheck's engine currently runs on Python 3.5 and uses SQLite3 as a database backend. Report website is using Ruby on Rails and Bootstrap.
Crawlcheck uses a number of open source projects to work properly. Python dependencies are listed in [requirements.txt](https://github.com/eghuro/crawlcheck/blob/architecture-refactoring/requirements.txt), Ruby dependencies are listed in [Gemfile](https://github.com/eghuro/crawlcheck/blob/architecture-refactoring/src/report/Gemfile)

And of course Crawlcheck itself is open source with a [public repository](https://github.com/eghuro/crawlcheck) on GitHub.

### Installation

1) Fetch sources
```sh
$ git clone https://github.com/eghuro/crawlcheck crawlcheck
```

2) Run install script
```sh
cd crawlcheck
./install.sh [database-file-location]
```
You will need python3, python-pip and sqlite3, ruby, libmagic, libtidy and zlib installed. All dev or devel versions.

### Configuration
Configuration file is a simple YAML file.
```sh
---
version: 1.02        # configuration format version
database: crawlcheck # sqlite database file
maxDepth: 10         # max amount of links followed from any entry point
agent: Crawlcheck    # user agent used

content-types:
 -
   "content-type": "text/html"
   plugins: # plugins to use for given content-type
     - linksFinder
     - htmlValidator
     
 -
   "content-type": "text/css"
   plugins:
     - tinycss

urls:
-
  url: "http://mj.ucw.cz/vyuka/"
  plugins: # which plugins are allowed for given URL
       - linksFinder
       - tidyHtmlValidator
       - tinycss
-
    url: "http://mj.ucw.cz/" #forbid entry here

entryPoints: # where to start
# Note, that once URI get's to the database it's no longer being requested 
# (beware of repeated starts, if entry point remains in the database execution won't 
# start from this entry point)
 - "http://mj.ucw.cz/vyuka/"
```

### Running crawlcheck
Assuming you have gone through set-up and configuration, now run checker:
```sh
$ cd [root]/crawlcheck/src/
$ python checker/ [config.yml]
```
Note: ```[root]/crawlcheck``` is where repository was cloned to, ```[config.yml]``` stands for the configuration file path

### Running report website
Assuming you have gone through set-up and configuration and checker either finished or is still running (otherwise there are just no data to display), now run report app:
```sh
$ cd [root]/crawlcheck/src/report/
$ bin/rails server
```
Note: you can specify port by adding ```-p [number]``` and interface by specifying ```-b [ip address]```

### Generating report to PDF
There is also a very simple Python script to generate a PDF containing all invalid links and other defects.
To run the script you need MySQL connector (you already have, since you ran checker) and ``pylatex``.
You can install pylatex using PIP:
```sh
$ pip install pylatex
```
You should also have ```pdflatex``` on your system.

Now run the script as follows:
```sh
$ cd [root]/crawlcheck/src
$ python TexReporter.py <dbfile> <outputfile>
```
For output file ``.pdf`` is added automatically.


### Plugins

There are currently 4 types of plugins: crawlers, checkers, headers and filters. Crawlers are specializing in discovering new links. Checkers check syntax of various files. Headers check HTTP headers and together with filters serve to customize the crawling process itself.

Crawlcheck is currently extended with the following plugins:

* linksFinder
* tidyHtmlValidator
* tinycss
* css_scraper
* contentLength
* depth
* robots

### How to write a plugin

Go to ``crawlcheck/src/checker/plugin/``, create ``my_new_plugin.py`` and ``my_new_plugin.yapsy-plugin`` files there.
Fill out .yapsy-plugin file:
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

    category = PluginType.CHECKER
    id = myPlugin

    def setJournal(self, journal):
        # record journal somewhere - all categories

    def setQueue(self, queue):
        # record queue somewhere - only crawlers

    def setConf(self, conf):
        # record configuration - only headers and filters

    def check(self, transaction):
        # implement the checking logic here for crawlers and checkers

    def filter(self, transaction, r):
        # implement the filtering logic here for headers (r is response from HEAD request)
        raise FilterException() # to forbid processing this transaction

    def filter(self, transaction):
        # implement the filtering logic here for filters
        raise FilterException() # to forbid processing this transaction
```

See http://yapsy.sourceforge.net/IPlugin.html and http://yapsy.sourceforge.net/PluginManager.html#plugin-info-file-format for more details.

### TODOs

 - Improve Tests and Documentation
 - Parallelization
 - Report - get full path from entry point to invalid link
 - More runtime rules in configuration - cookies related
 - Report - manual annotations of findings
 - Filters and search in report
 - Detect sitemap.xml (from robots.txt), validate it, note the links from sitemap
 - Generate sitemap.xml
 - Detect forms and Javascript actions

License
----

MIT
