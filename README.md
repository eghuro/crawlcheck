# Crawlcheck

Crawlcheck is a web crawler invoking plugins on received content. It's intended for verification of websites prior to deployment. The process of verification is customisable by configuration script that allows complex specification which plugins should check particular URIs and content-types. Main engine and plugins are written in Python, there's also possibility to show report in form of website written in Ruby on Rails or generate report in PDF. The report contains discoveries plugins made during the verification.

### Version
0.01

### Tech

Crawlcheck's engine currently runs on Python 2.7 and uses MySQL as a database backend. Report website is using Ruby on Rails.
Crawlcheck uses a number of open source projects to work properly:
* [Yapsy] - plugin framework
* [marisa_trie] - Trie implementation
* [py_w3c] - for html validation plugin
* [tinycss] - for css validation plugin
* [beautifulsoup4] - for links finder plugin
* [requests], [urllib3] - fpr networking
* [enum] - duh
Following gems are needed for report
* [rails]
* [mysql2]
* [sass-rails]
* [uglifier]
* [coffee-rails]
* [jquery-rails]
* [turbolinks]
* [jbuilder]
* [sdoc]

And of course Crawlcheck itself is open source with a [public repository](https://github.com/eghuro/crawlcheck) on GitHub.

### Installation

You need mysql-server, python-2.7, python-mysql and ruby installed.

Following packages needs also to be installed. It can be done through pip (you need python-pip and python-dev):
```sh
$ pip install marisa_trie yapsy py_w3c enum urllib3 requests tinycss beautifulsoup4
```
For report, rails also needs to be installed
```sh
$ gem install rails
```
Clone and install Crawlcheck as follows: (make sure to prepare configuration file and setup mysql database beforehand)
```sh
$ git clone [git-repo-url] crawlcheck
$ cd crawlcheck/src
```

Install report
```sh
$ cd report
$ bin/bundle install
```
Edit ```config/database.yml``` to set up database credentials
Install database
```sh
$ bin/rake db:drop db:create db:schema:load
```

Set up MySQL tables - make sure to specify user, the script assumes "crawlcheck" as db name
```sh
$ cd ..
$ mysql < checker/mysql_tables.sql
```
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

### Running crawlcheck
Assuming you have gone through set-up and configuration, now run checker:
```sh
$ cd [root]/crawlcheck/src/
$ python checker/ [config.xml]
```
Note: ```[root]/crawlcheck``` is where repository was cloned to, ```[config.xml]``` stands for the configuration file path

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
Now run the script as follows:
```sh
$ cd [root]/crawlcheck/src
$ python TexReporter.py <dbUri> <dbUser> <dbPassword> <dbname> <outputfile>
```
For output file ``.pdf`` is added automatically.


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
