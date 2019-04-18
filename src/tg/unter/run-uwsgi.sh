#!/bin/bash
#
# Run the Unter web app under the uWSGI
# web server.

# Set up the configuration and virtual-environment
# directories if they are not already set.
if [ "${ROOT_DIR}" == "" ] ; then
	ROOT_DIR=$(realpath .)
fi
if [ "${VENV_DIR}" == "" ] ; then
	VENV_DIR=$(dirname $(dirname $(which python)))
fi
echo ROOT_DIR $ROOT_DIR
echo VENV_DIR $VENV_DIR
uwsgi --paste "config:${ROOT_DIR}/development.ini" --socket 127.0.0.1:8053 --http-socket 127.0.0.1:8052 --virtualenv "${VENV_DIR}" -b 32768
