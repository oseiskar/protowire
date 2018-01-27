#!/bin/bash
set -e
set -v

# unit tests
nosetests

# linter
pylint *.py
