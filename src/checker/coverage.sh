#!/bin/bash
rm crawlcheck
sqlite3 crawlcheck < mysql_tables.sql
source ../../py3env/bin/activate
python -c "import yaml; import marisa_trie; print('Imported')"
pip install coverage
coverage3 erase
coverage3 run --omit="../../py3env/*" acceptorTest.py
coverage3 run --omit="../../py3env*" -a configLoaderTest.py
coverage3 run --omit="../../py3env/*" -a coreTest.py
##coverage run -a downTest.py
##coverage run -a pluginDBAPItest.py
##coverage run -a pluginRunnerTest.py
#coverage run -a py_w3c_html_validator_pluginTest.py
#coverage run -a plugin/test_css_scraper.py
#coverage run -a paramDetectionTest.py
coverage3 report --omit="../../py3env/*" -m
