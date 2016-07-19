#!/bin/bash

# Exit if undeclared variables are used
set -o nounset

# Exit if any command exits with error
set -o errexit

# Print each command to stdout before executing it
# set -o verbose

function control_c() {
	exit 1
}

trap control_c SIGINT

cd "$(dirname $0)"
for FILE in *.js; do
	../untangle.py -c "$FILE" "temp/$FILE" >/dev/null 2>&1
	cmp -s "temp/$FILE" "out/$FILE" && echo "$FILE OK" || echo "$FILE FAILED"
done
