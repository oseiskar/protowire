#!/bin/bash
set -e
set -v

# install locally
pip install -e .[dev]

# run tests normally
./run-tests.sh
