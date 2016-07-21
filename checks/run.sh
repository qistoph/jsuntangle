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

ret=0
cd "$(dirname $0)"
for FILE in *.js; do
	echo -n "$FILE "

	set +o errexit
	OUTPUT=$(../bin/jsuntangle -c "$FILE" "temp/$FILE" 2>&1)
	EXIT=$?
	set -o errexit

	if [ $EXIT -eq 0 ]; then
		cmp -s "temp/$FILE" "out/$FILE" && echo "OK" || echo "CHANGED"
	else
		echo "FAILED"
		echo "$OUTPUT"
		echo
		ret=1
	fi
done

exit $ret
