#!/bin/sh

pip install marisa_trie yapsy py_w3c enum34 urllib3 requests tinycss beautifulsoup4 pyyaml
gem install rails

#git clone https://github.com/eghuro/crawlcheck $1

cd src/report
bin/bundle install

cp ../checker/mysql_tables.sql db/structure.sql
sqlite3 ../crawlcheck < ../checker/mysql_tables.sql
bin/rake db:migrate
bin/bundle exec rake db:schema:load
bin/rake db:drop db:create db:schema:load
sqlite3 ../crawlcheck < ../checker/mysql_tables.sql
bin/rake db:migrate RAILS_ENV=development
