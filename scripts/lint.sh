#!/usr/bin/env bash

set -x

ruff check match
mypy match

black match --check
