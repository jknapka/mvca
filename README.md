**Unter**

(Note: the "for public consumption" name is the Migrant Volunteer
Coordinating Assistant.)

Unter is a pun on "Uber". Originally it occurred to me that a
*free* ride-hailing service would be really useful in El Paso
for getting migrants to their transit points (airport, bus
station), so the name was obvious - "unter" == "under", under the bridge,
underclass, under-served, under-appreciated. But we need to do
more than ride-sharing: we need volunteer coordinators to be
able to signal events, to know which volunteers are available
at which times, and to access various other kinds of resources
than rides (such as interpreters).

This will start as a pure web app that:

  * Allows volunteers to register and indicate their availability
    windows (times and durations).
  * Allows volunteer coordinators to see available volunteers for
    given time periods.
  * Allows volunteers coordinators to signal "need events" (eg:
    "Ride to airport for 3 individuals from La Quinta to be
    delivered by 10:15 AM").
  * Matches need events with available volunteers and alerts those
    volunteers via email or text.
  * Allows volunteers to commit to respond to a need event by
    clicking a link.
  * Allows volunteer coordinators to see which volunteers have
    responded to need events.
  * Future work:
    * An Android app that polls for relevant events and issues
      alerts on the phone.
    * iOS too.
    * Track volunteer progress - are they actually coming and
      if so, where are they now?
    * Be as smart as possible about computing which volunteers
      are "available" for particular need events - eg we don't
      want to alert a user for an event starting in 15 minutes
      if we know it will take them 30 minutes to drive to the
      location.

**Development**

The webapp is built on TurboGears 2.4 using Python 3.7 (actually
Python 3.4 or better should be OK). TurboGears is a fairly standard
"batteries included" kind of Python web framework, similar to
Flask. Visit http://www.turbogears.org for docs.

To work on the web app, you need to install virtualenv:

`pip install virtualenv`

and then set up a Python 3 virtual environment:

`virtualenv -p /path/to/your/python3.exe ./python3-venv`

Then activate the virtual environment:

`. ./python3-venv/bin/activate`

Then install Unter's dependencies:

```
cd path/to/your/unter/checkout/src/tg/unter
pip install --pre turbogears
pip install tg.devtools
python setup.py develop
gearbox setup-app
gearbox serve
```

Now you should have an Unter server running on port 8080.

The primary functionality is implemented in src/tg/unter/unter/controllers/root.py.
I've also split off some utility code in additional files in the
controllers/ directory. Those files don't implement TurboGears
controllers, they are just buckets to organize code that root.py
uses.

The DB model is in src/tg/unter/unter/model. It uses SQLAlchemy
as the object-relational mapper.
