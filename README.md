# Crawlcheck

Crawlcheck is a web crawler invoking plugins on received content. It's intended for verification of websites prior to deployment. The process of verification is customisable by configuration script that allows complex specification which plugins should check particular URIs and content-types. Main engine and plugins are written in Python, there's also possibility to show report in form of website written in Ruby on Rails or generate report in PDF. The report contains discoveries plugins made during the verification.

### Version
0.01

### Tech

Crawlcheck's engine currently runs on Python 2.7 and uses MySQL as a database backend.
Crawlcheck uses a number of open source projects to work properly:
* [Yapsy] - plugin framework
* [marisa_trie] - Trie implementation
* [py_w3c] - for html validation plugin
* [tinycss] - for css validation plugin
* [beautifulsoup4] - for links finder plugin
* [requests], [urllib3] - fpr networking
* [enum] - duh

And of course Crawlcheck itself is open source with a [public repository](https://github.com/eghuro/crawlcheck) on GitHub.

### Installation

You need mysql-server, python-2.7, python-mysql installed.

Following packages needs also to be installed. It can be done through pip (you need python-pip and python-dev):
```sh
$ pip install marisa_trie yapsy py_w3c enum urllib3 requests tinycss beautifulsoup4
```
Clone and run Crawlcheck as follows: (make sure to prepare configuration file beforehand)
```sh
$ git clone [git-repo-url] crawlcheck
$ cd crawlcheck/src
$ python checker/ [config.xml]
```

TODO report ....

### Plugins

Crawlcheck is currently extended with the following plugins

* linksFinder
* py_w3c_htmlValidator
* tinycss_cssValidator
`

### Todos

 - Improve Tests and Documentation
 - Report - manual annotations of findings
 - Filters and search in report
 - Scrap inline css
 - Regular expressions in configuration for plugins (URLs)

License
----

MIT
