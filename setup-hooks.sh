#!/bin/bash

# Set up git hooks for Unter/MVCA. This should be done firs
# thing upon checking out the project source tree. It must
# be run from the source tree root (the directory containing
# this file).
[[ -e src/tg/unter ]] || {
	echo "Run this script from the root of the checked-out source tree."
	exit 1
}

ln -s ../../hooks/pre-commit.sh .git/hooks/pre-commit

exit 0
