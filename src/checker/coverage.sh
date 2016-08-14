#!/bin/sh
rm crawlcheck
sqlite3 crawlcheck < mysql_tables.sql
coverage erase
coverage run acceptorTest.py
coverage run -a configLoaderTest.py
coverage run -a downTest.py
coverage run -a pluginDBAPItest.py
coverage run -a pluginRunnerTest.py
coverage run -a py_w3c_html_validator_pluginTest.py
coverage run -a plugin/test_css_scraper.py
coverage run -a paramDetectionTest.py
coverage report -m
