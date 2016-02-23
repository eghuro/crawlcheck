# Crawlcheck

Crawlcheck is a web crawler invoking plugins on received content. It's intended for verification of websites prior to deployment. The process of verification is customisable by configuration script that allows complex specification which plugins should check particular URIs and content-types. Main engine and plugins are written in Python, there's also possibility to show report in form of website written in Ruby on Rails or generate report in PDF. The report contains discoveries plugins made during the verification.

![travis-ci](https://api.travis-ci.org/eghuro/crawlcheck.svg?branch=master) ![codecov](https://img.shields.io/codecov/c/github/eghuro/crawlcheck/master.svg)

### Version
0.03

### Tech

Crawlcheck's engine currently runs on Python 2.7 and uses SQLite3 as a database backend. Report website is using Ruby on Rails and Bootstrap.
Crawlcheck uses a number of open source projects to work properly:
* [Yapsy] - plugin framework
* [sqlite3] - data storage
* [pyyaml] - configuration 
* [marisa_trie] - Trie implementation
* [py_w3c] - for html validation plugin
* [tinycss] - for css validation plugin
* [beautifulsoup4] - for links finder plugin
* [requests], [urllib3] - for networking
* [enum34] - enum compatible with Python 3

Following gems are needed for report
* rails
* sqlite3
* sass-rails
* uglifier
* coffee-rails
* jquery-rails
* turbolinks
* jbuilder
* sdoc
* will_paginate-bootstrap
* bootstrap-sass
* autoprefixer-rails


And of course Crawlcheck itself is open source with a [public repository](https://github.com/eghuro/crawlcheck) on GitHub.

### Installation

1) Install dependencies
* You need mysql-server, python-2.7, sqlite3 (dev) and ruby installed.
* Following packages needs also to be installed. It can be done through pip (you need python-pip and python-dev):
```sh
$ pip install marisa_trie yapsy py_w3c enum34 urllib3 requests tinycss beautifulsoup4 pyyaml
```
* For report, rails also needs to be installed
```sh
$ gem install rails
```
2) Install crawlcheck
* Clone and install Crawlcheck as follows: (make sure to prepare configuration file beforehand)
```sh
$ git clone [git-repo-url] crawlcheck
$ cd crawlcheck/src
```
* Install report
```sh
$ cd report
$ bin/bundle install
```
* Install database

  First sqlite command will create tables, rake command will do initialization needed for ruby, second sqlite call will set up initial values in certain tables and ensures integrity constraints remains unchanged.
```sh
$ sqlite3 <dbfile> < ../checker/mysql_tables.sql
$ DATABASE_URL="sqlite3://<dbfile>" bin/rake db:drop db:create db:schema:load
$ sqlite3 <dbfile> < ../checker/mysql_tables.sql
```

### Configuration
Configuration file is a simple YAML file.
```sh
---
version: 1.01        # configuration format version
database: crawlcheck # sqlite database file

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
       - htmlValidator
       - tinycss

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
Note: ```[root]/crawlcheck``` is where repository was cloned to, ```[config.xml]``` stands for the configuration file path

### Running report website
Assuming you have gone through set-up and configuration and checker either finished or is still running (otherwise there are just no data to display), now run report app:
```sh
$ cd [root]/crawlcheck/src/report/
$ DATABASE_URL="sqlite3://<dbfile>" bin/rails server
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

Crawlcheck is currently extended with the following plugins:

* linksFinder
* htmlValidator
* tinycss
* css_scraper

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
class MyPlugin(IPlugin):

    def setDb(self, DB):
        # record DB somewhere

    def getId(self):
        """ The id is used in configuration - in this case <plugin id = "myPlugin"/>
        """

        return "myPlugin"

    def check(self, transactionId, content):
        # implement the logic here
```

See http://yapsy.sourceforge.net/IPlugin.html and http://yapsy.sourceforge.net/PluginManager.html#plugin-info-file-format for more details.

### TODOs

 - Improve Tests and Documentation
 - Report - manual annotations of findings
 - Filters and search in report
 - Regular expressions in configuration for plugins (URLs)

License
----

MIT
