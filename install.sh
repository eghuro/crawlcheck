#!/bin/sh
virtualenv -p /usr/bin/python3 py3env
source py3env/bin/activate

pip install -r requirements.txt
gem install bundler
gem install rails

cd src/report
python ./patch-cfgs.py $1 #TODO: hardend

bin/bundle install

cp ../checker/mysql_tables.sql db/structure.sql
sqlite3 $1 < ../checker/mysql_tables.sql 2>/dev/null
bin/rake db:migrate
bin/rake db:migrate RAILS_ENV=development
sqlite3 $1 < ../checker/mysql_tables.sql 2>/dev/null
