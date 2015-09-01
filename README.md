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
Clone and run Crawlcheck as follows: (make sure to prepare configuration file and setup mysql database beforehand)
```sh
$ git clone [git-repo-url] crawlcheck
$ cd crawlcheck/src
# Set up MySQL tables - just first time - make sure to specify user, the script assumes "crawlcheck" as db name
$ mysql < checker/mysql_tables.sql 

$ python checker/ [config.xml]
```

TODO report ....

### Configuration

Configuration file is a simple XML file.
```sh
<crawlcheck version="0.01">
  <db user="test" pass="" uri="localhost" dbname="crawlcheck" />
```
``crawlcheck`` is root element and contains a version specification.
Then we specify how we connect to the database in ``db`` element
```sh
  <plugins>
    <resolutions>
      <uris default="True" />
      <contentTypes default="False">
        <contentType key="text/html" accept="True" />
      </contentTypes>
    </resolutions>
```
Inside ``plugins`` element we store all plugin configuration and default configuration. These global defaults are used if plugin-specific configuration doesn't say enough to make a resolution if a page (URI + content-type) should be passed to the plugin. ``uris`` and ``contentTypes`` elements are obligatory and ``default`` tag in both of them as well, but that's all what's obligatory in the configuration. The rest is up to you.
```sh
    <plugin id="linksFinder">
      <resolutions>
        <uris default="False">
          <uri key="http://ksp.mff.cuni.cz" accept="True" />
          <uri key="http://ksp.mff.cuni.cz/mwforum/" accept="False" />
          <uri key="http://ksp.mff.cuni.cz/about/ksp-spot-hq.ogv" accept="False" />
        </uris>
        <contentTypes default="False">
          <contentType key="text/html" accept="True" />
        </contentTypes>
      </resolutions>
    </plugin>
```
Plugin specific configuration is inside ``plugin`` element (with obligatory ``id`` attribute) There should be ``resolutions`` element, which is same as on global level, with only exception that no options are mandatory. Note that you can always specify URI and Content-Type specific rules with plugin-specific fallback and global rules and global fallback. In each rule one can specify ``accept`` True or False. In evaluation we go from the most specific rule (plugin -> URI / content-type) to more general (plugin -> default ... global -> URI/content-type ... global -> default) and when True or False is given, that's a definite resolution.
```sh 
    <entryPoints>
      <entryPoint uri="http://ksp.mff.cuni.cz/" />
    </entryPoints>
</crawlcheck>
```
Last thing you specify are ``entryPoints`` - these are URIs Crawlcheck will request on start and link checking and other verification goes from there. Note, that once URI get's to the database it's no longer being requested (beware of repeated starts, if entry point remains in the database execution wont start from this entry point)

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

