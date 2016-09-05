#!/bin/sh
virtualenv -p /usr/bin/python3 py3env
source py3env/bin/activate

pip install -r requirements.txt
gem install bundler
gem install rails

python ./patch-cfgs.py $1 #TODO: hardend

sqlite3 $1 < src/checker/mysql_tables.sql
sqlite3 $1 < src/checker/sql_values.sql

cd src/report

bin/bundle install

cp ../checker/mysql_tables.sql db/structure.sql
bin/rake db:migrate
bin/rake db:migrate RAILS_ENV=development

#cd ../../
#sqlite3 $1 < src/checker/sql_values.sql
