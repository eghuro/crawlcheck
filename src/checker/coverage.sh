#!/bin/sh
rm test.sqlite
sqlite3 test.sqlite < mysql_tables.sql
coverage erase
coverage run acceptorTest.py
coverage run -a configLoaderTest.py
coverage run -a downTest.py
coverage run -a pluginDBAPItest.py
coverage run -a pluginRunnerTest.py
coverage run -a py_w3c_html_validator_pluginTest.py
coverage report --skip-covered -m
