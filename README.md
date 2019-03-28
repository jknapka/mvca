**Unter**

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
