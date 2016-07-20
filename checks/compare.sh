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

function yesno() {
	if [ $# -ge 2 ]; then
		case $2 in
			y|Y) default="y"; opts="Y/n";;
			n|N) default="n"; opts="y/N";;
			*)   default="";  opts="y/n";;
		esac
	else
		default=""
		opts="y/n"
	fi

	while [ 1 ]; do
		echo -n "$1 [$opts]: "
		read ans

		[ -z "$ans" ] && ans="$default"

		case "$ans" in
			y|Y) return 0;; # Return non-error
			n|N) return 1;; # Return error
		esac
	done
}

cd "$(dirname $0)"
for FILE in *.js; do
	echo -n "$FILE "

	set +o errexit
	../untangle.py -c "$FILE" "temp/$FILE" >/dev/null 2>&1
	EXIT=$?
	set -o errexit

	if [ $EXIT -eq 0 ]; then
		set +o errexit
		cmp -s "temp/$FILE" "out/$FILE"
		EXIT=$?
		set -o errexit
		if [ $EXIT -ne 0 ]; then
			vimdiff "out/$FILE" "temp/$FILE"
			yesno "Continue?" || break
		else
			echo "No change"
		fi
	else
		echo "FAILED"
	fi

done
