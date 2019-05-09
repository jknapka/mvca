'''
The Unter asynchronous alert service.

This is a daemon that issues alerts via email
or SMS (and potentially other media) for the
Unter web service.

Requirements:

    * Watch a configurable staging directory for
    JSON files containing information about alerts
    to be issued. Scan the staging directory
    once every N seconds (configurable).

    * When a new alert file is found, unlink it
    and process the contents, which will look like
    this:

    {
        email: "foo@bar.com",
        phone: "+12345678901",
        subject: "An email subject line",
        message: "Message body here."
    }

    * Issue alerts by calling configurable alert
    API entry points for each alert medium (SMS,
    email, etc.).

    * Log alert activity to a configurable filename.
    Log data should be easily consumable by other
    programs.

    * Write a status file at configurable intervals.
    The content of that file should be JSON and in
    the following format:

    {
        successfulAlertCount: n,
        failedAlertCount: n
    }
'''
from pathlib import Path

def scanDir(dname):
    ''' Scan dname and return a list of alert files. '''
    result = []
    p = Path(dname)
    if p.exists() and p.is_dir():
        files = p.glob('*.json')
        result = list(map(str,files))
    return result


