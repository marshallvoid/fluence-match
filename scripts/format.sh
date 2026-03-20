#!/usr/bin/env bash

set -x

ruff format match

ruff check match --select I --fix

black  --skip-string-normalization match
