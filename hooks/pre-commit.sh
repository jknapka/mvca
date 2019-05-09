#!/bin/bash

# Pre-commit hook.

# If we're on the master branch, run tests.
BRANCH=$(git status | grep "On branch" | cut -d' ' -f3)

if [ "$BRANCH" == "master" ] ; then
	if ! ../../hooks/run-tests.sh ; then
		echo Committing on master with failed tests - ABORTING COMMIT.
	fi
fi

