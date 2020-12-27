#!/bin/bash

# Helper file for development tests: call `hackimposition`.
export PYTHONPATH="$(cd $(dirname $0)/.. && pwd):$PYTHONPATH"
python -m hackimposition $*
