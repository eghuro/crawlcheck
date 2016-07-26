#!/bin/sh

sudo pip install marisa_trie yapsy py_w3c enum34 urllib3 requests tinycss beautifulsoup4 pyyaml
sudo gem install bundler
sudo gem install rails

cd src/report
bin/bundle install

cp ../checker/mysql_tables.sql db/structure.sql
sqlite3 ../crawlcheck < ../checker/mysql_tables.sql 2>/dev/null
bin/rake db:migrate
bin/rake db:migrate RAILS_ENV=development
sqlite3 ../crawlcheck < ../checker/mysql_tables.sql 2>/dev/null
