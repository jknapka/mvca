#!/bin/bash

# Run all Unter/MVCA tests. This is called by git's pre-commit hook.

# Ensure we're in the root of the source tree.
pushd ${BASH_SOURCE%/*}
[[ -e src/tg/unter ]] || {
	# We ended up in .git/hooks?
	if [ -e ../../src/tg/unter ] ; then
		cd ../..
	else
		echo "Cannot find root of Unter/MVCA source tree. Exiting."
		exit 1
	fi
}

# Run tests for all Unter/MVCA components.

# Test the web app. This is a template for further test
# sections:
#
# pushd to the relative directory containing the tests.
# Run the tests.
# If they fail, popd and exit with an error.
# Otherwise, just popd.
pushd src/tg/unter
if ! nosetests ; then
	popd
	exit 1
fi
popd

exit 0

