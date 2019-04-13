Installation and development instructions can be found below.

Unter is a system for coordinating volunteer efforts for the
migrants passing through El Paso. Its "official" name will be
something like the "Migrant Volunteer Coordination Assistant",
but I was thinking of "Unter" as a pun on the Uber ride-
sharing service.

Unter supports the following functions:

* Registering volunteers and allowing volunteers to indicate
  times during the week when they are available to serve.

* Registering coordinators who can create "need events"
  describing needs for volunteer services at particular
  dates and times.

* Alerting volunteers when an event needs volunteer help
  during a date and time when they have indicated they
  are available.

* Allows volunteers to respond to need events, thereby
  committing to serve the need.

* Allows coordinators to see which events require volunteer
  commitment, and which already have committed volunteers.

* Allows coordinators (but not other volunteers) to see
  contact information for any volunteer.

TO DO:

) Volunteers should be able to see and respond only to
events that are active and not already fully-staffed by
volunteers.

Story (DONE): Veronica the Volunteer logs into Unter.
  - On her volunteer info page, she can see a list of events that
    occur during her times of availability.
  - She does not see events that do not occur during her
    times of availability.
  - She does not see events that overlap with events to which
    she has already committed.
  - She does not see events that are already being fully-served by
    other volunteers, even if she would be available for them.
  - She can click a link in an event row to confirm her ability to
    serve at the event.
  - She can click a different link to indicate that she will not
    be able to serve at the event (in which case she will not
    receive any further alerts for that particular event).

) ALERTS IN GENERAL:
  - Volunteers should receive alerts for events they may be
    available to serve.
    - Under what circumstances?
      - Newly-created events should be alerted.
      - Alerts every N hours for understaffed events? Might be
        super-annoying and cause people to un-subscribe or
        decline to volunteer.
  - Volunteers should receive reminder alerts for events to which
    they've committed an hour or so prior to the event.
  - Volunteers should never receive alerts for events from which
	they have decomitted.
  * This will require a monitor process somewhere. Maybe just a
	cron job that pokes a URL on the web service every five
	minutes or something.

Story (TO BE WRITTEN)...

) Check that when a need event is created, volunteers who
are available at the time of the event and who are not
already committed to an event will receive an alert.

Story (INCOMPLETE):
  - (done) Carla creates a need event for a family needing
    a ride to the airport on Sunday morning at 10:00 AM, which
    will take about 1 hour.
  - (done) Vincent, Veronica, and Velma are available at that time.
    However, Vincent has already committed to drive two
    individuals to the bus station at 10:15. 
  - (done) Veronica and Velma have not committed to any events that
    overlap the interval from 10:00 AM to 11:00 AM on Sunday 
    morning, so they should receive alerts. 
  - Alerts are sent via email, and via text (if the volunteer
    has indicated text alert preference).
  - (done) Volunteer phone numbers are visible on the event
    page to logged-in coordinators, so they can make confirmation
    phone calls to volunteers.
  - (done) Coordinator phone numbers are visible to volunteers for
    the events to which they have committed. Only the phone
    numbers for the coordinators who created those events
    are visible to volunteers, and only to the volunteers
    who commit to the events.

) Check that we can issue alerts for existing events as
needed and that case (1) is handled correctly for each
event. That is, we want to be able to issue alerts not only
for new events, but for existing events that are not
yet claimed by volunteers.

Story (INCOMPLETE): No volunteers have responded to Carla's Sunday
morning airport event as of Saturday morning. She goes
to the event page (which shows all active event) and:

  - (done) sees that an alert was last sent for that particular event
    on Friday morning.
  - (done) She can send a new alert for that event from the event list page,
    with a single click.
  - Again, Veronica and Velma should recieve alerts.
  - Carla should be able to click the event to see a list of 
    available volunteers for the event time, and their contact
    information.
  - That list should include volunteers who have already committed
    to the event, clearly marked as having committed.

Story (NOT STARTED): While looking at the event page, Carla notices
that there are some other events on Sunday and Monday
for which no volunteers have committed.

  - She can issue alerts for all active and under-volunteered
    events with a single click from the event page.
  - Alerts are sent only for events that have NOT had alerts sent
    within the past N hours, so Carla's airport event does
    NOT cause an additional alert to be generated (since
    she just sent an alert for that specific event, in
    the story above).
  - NOTE: Show events in reverse temporal order on the event page.
    Also provide a "today's events only" link.
  - CONSIDER: avoid alerting *volunteers* who have been alerted
    recently, to avoid event fatigue.

) Check that when multiple volunteers respond to an event,
we confirm the event for only the number of volunteers
needed (via text or email), and that we inform extra
volunteers that they are NOT required for the event they
responded to. First-come-first-accepted is probably adequate.

Story (NOT STARTED): Both Veronica and Velma respond to Carla's airport
event within a short period of time. Only one volunteer
is necessary for this event, so:

  - one of them should receive a confirmation message saying
    "Thank you for responding. Please be at <location> at 10:00
    Sunday morning. If you find you can't make it, please call
    <Carla's phone>, and please log in here and remove yourself
    from the event."
  - The other should receive a message saying "Thank you for
    responding! This need is already being served by other
    volunteers. There's nothing more you need to do right now." 
  * For test purposes, we'll need an "Alerter" interface that
    can be stubbed for testing and actually send alerts in
    production.

) Show volunteers who have responded to events on the
need_events page, and on the event page for a particular
event.

Story (INCOMPLETE): When looking at the event page showing all events,
Carla (a coordinator) can:

  - see that (say) Veronica has responded to her airport event.
  - She can click Veronica's name to see contact information.

Story (INCOMPLETE): Veronica (a normal volunteer, not a coordinator)

  - CANNOT see who has responded to events.
  - She can only see which events require volunteers to
    respond, and how many volunteers have responded. She
    cannot see contact information for other volunteers.

) Show volunteers who are available to respond to events
on the event page for a particular event.

Story (INCOMPLETE): When looking at the event page, Carla (a coordinator)
can:

  - click on an event row to see more-detailed information
    for the event.
  - She can see a list of volunteers who have responded to
    the event, including their contact information.
  - She can also see a list of volunteers who are available at
    the event's time and have no overlapping commitments,
    including their contact information.

Non-coordinators like Veronica CANNOT see this detailed
event information.

) Show volunteers which events they've committed to.

Story (INCOMPLETE): On her volunteer information page, Veronica can

   - see a list of the upcoming events she has committed to.
   - See contact information for the coordinators who created
     those events.
   - Coordinators can also see this information by visiting
     the "volunteer_info" page for a specific volunteer.

) Allow volunteers to de-commit from an event. This
should cause the coordinator who created the event to
receive an alert. It should also alert any other
volunteers who may be available at the event's time.

Story (INCOMPLETE): (some implementation of responses and
decommits are present in need.py, and test_commit.py exists.)

Veronica realizes that she is actually going to
be out of town on Sunday and should not have committed
to Carla's airport event. She logs into Unter and:
  - in her volunteer information page, she can see the event
    as one she has committed to.
  - She can click a "Can't make it" link to inform Unter
    that she will not be serving that particular event.
  - Since Carla created the event, Carla should receive
    an alert (again, via email and possibly text) indicating
    that the event is again in need of volunteer help.
  - Unter should also immediately treat the event as a new
    event and issue any necessary alerts to volunteers who
    may be available.

*) Allow volunteers to hide events? That is, to pre-emptively
say "No, I can't help with this" and then not be bothered
about it again.

Story (NOT STARTED, OPTIONAL?): Veronica receives an alert for a bus-station
ride on Saturday afternoon. She knows she's actually unavailable
at that time, even though Saturday afternoons are usually free.
  - She can go to the web app's "sorry" page for the specific
    event to indicate that she definitely is not available at
    the indicated time.
  - She will not receive any further alerts regarding the event.
  - A link to the "sorry" action (as well as to the "commit"
    action) is included in text and email alerts.

*) Show a "day planner" view of a coordinator's events.

*) Show a "day planner" view of a volunteer's events.

*) Track whether volunteers who commit to events actually
show up. If they don't show up for N events, disable their
volunteer account. De-committing from an event SHOULD NOT
count as "not showing up" for this purpose.

Story (NOT STARTED): Vincent just blows off his bus station event to
go to brunch with some friends. Because he didn't de-
commit from the event, the people involved are left in
the lurch and they miss their bus. 
  - Christopher, who created the bus-station event, marks
    Vincent as a "no-show" via the coordinator view of 
    Vincent's "volunteer_info" page.
  - If this happens N or more times, Vincent is deactivated
    as a volunteer and will no longer receive alerts.
  - No-shows have to be manually flagged by a coordinator;
    Unter will not do this automatically merely because
    a volunteer de-commits from an event. De-committing is
    the responsible way to indicate inability to serve.

Event Management API
====================

It seems clear we need a clean API for managing events.

) Get events that are
  - not complete
  - not fully-committed with enough volunteers

) For each such event, get volunteers who:
  1) Have committed to the event; or
  2) Are uncommitted but available, meaning:
     a) Are available at the event time and for at least
        the duration of the event;
     b) Are NOT committed to any overlapping event.



Installation and Setup
======================

Requires Python 3.5 or better. Ideally, run this inside a
Python3 virtual environment created using:

virtualenv -p /path/to/python3.exe ./python3-venv-for-unter
. ./python3-venv-for-unter/bin/activate

Then follow the instructions below.

Install ``unter`` using the setup.py script::

    $ cd unter
    $ python setup.py develop

Create the project database for any model classes defined::

    $ gearbox setup-app

Start the paste http server::

    $ gearbox serve

While developing you may want the server to reload after changes in package files (or its dependencies) are saved. This can be achieved easily by adding the --reload option::

    $ gearbox serve --reload --debug

Then you are ready to go.
