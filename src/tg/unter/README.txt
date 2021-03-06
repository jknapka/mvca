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

* Unter intentionally does *not* track the identities of
  the people being served by volunteer activities. Each
  event will have a free-text field where coordinators
  can record relevant identifying information, but the
  event records will be thrown away when the event
  is complete. For one thing, we want to avoid endangering
  clients by keeping too much of a paper trail that might
  be used by unwelcome authorities to track people; and
  for another, we don't want to create a lot of pointless
  administrative labor for coordinators. Creating an
  event should be a one-minute-or-less activity.

* Unter intentionally tracks only the minimum necessary
  information for users (coordinators and volunteers) -
  just email addresses and phone numbers.

QUESTIONS:

1) Should coordinators be able to de-commit a volunteer from
an event? If so this has to be made to work, and if not,
removed. [(done) For now, remove "decommit" links if the logged-in
user is not the owner of the commitment.]

2) Should coordinators be allowed to respond to serve at
events (if they are also regular volunteers)? [Yes, probably.
(done, default behavior)]

3) Should volunteers be able to respond to events that
DO NOT occur during their available times? Eg just by clicking
the "Respond" link on the event list? Why not, if they
happen to know they're contingently available? Well, they
might accidentally commit to an event they actually are
not available for. [But we should allow this, maybe with
an additional confirmation. (done, default behavior, except
no confirmation)]

4) When logged in as themselves, should coordinators be able
to respond to events for *other* volunteers? Probably not?
[Disallow for now (done).]

----------
ISSUES

) Sending of alerts via email and SMS *needs* to be asynchronous.
Right now for demo purposes those functions are handled within
the web request directly, but if we try to do them synchronously
for a large number of volunteers and/or events, we are going to
hang a server thread for too long.

Right now our back-end DB is SQLite. I trust SQLite, it is super-
well-tested and robust but only for single-threaded use. So,
should probably switch to MySQL for development and production.
Maybe still test with SQLite for simplicity, even though that's
kind of dangerous due to SQLite's untyped columns. But if we
use a multi-user DB we can just have a separate alert-service
process that gets kicked off periodically. That service could
even be another TG app that supports a simple "/check_events"
API

Alternatively, we could stick with SQLite and make the alert
service accept the complete context of each alert in its
API - text and users to whome the alert should be issued, as
well as email addresses and phone numbers. This sounds like
a not-so-great approach, after writing the previous paragraph :-P

) It would be really good to provide a Spanish-language version of
the entire site. I am totally unqualified to do that, from a
language perspective. Providing "es" versions of templates should
be natively supported by TurboGears, so all I need is translation
assistance there. Internationalizing resource strings (eg for
dynamically-generated SMS messages) will require more effort.

  - I've got the i18n stuff to coexist with the functional English-
	language code, but I've yet to get it to actually perform any
	translations. It needs to be sensitive to the user browser's
	preferred language setting, and that for some reason doesn't
	seem to be working - we always get the English text even when
	there's a compiled es/unter.mo with some translations.

) I'm considering letting Unter assume a volunteer is available
any time, if they have not configured any available time periods.
That way, new volunteers will start to see alerts for need events
immediately, and some might not ever need to bother configuring
time availabilities.  We could also include a link to the
"configure your available times" page in each alert message (but
only for users with no configured time periods).

) (in progress) Provide a configurable site name and use [SITE_NAME] in
alert emails and SMSs. (Note, we can use the tg config
variable "project_name" for this.)

) (done) Initial volunteers need to be approved by a coordinator before
they are activated as volunteers. We may as well require a
password confirmation email, also.

) (done) Need a "password reset" function.

) (done) Need to allow users to edit their data.

) (done) Make event rendering consistent across all pages. We need
   - An "event_renderer" template that we can include.
   - That template should be sensitive to:
     - Whether the logged-in user is the same as the user that
       created the event, in which case a "Cancel" link should
       be available.
     - Whether the logged-in user is available for the event,
       in which case a "Respond" link should be available.
     - Whether the logged-in user is committed to the event,
		in which case a "Break commitment" link should be available.

) (done) "Respond" URIs in text messages are (a) very easy to guess and
(b) require a login. What we need to do is:
	1) Generate "respond" and "reject" UUIDs and associate them
	with the corresponding user ID and neID.
	2) Provide an exposed URI that doesn't require a login.
	3) When called with /respond?uuid=skjfghkljsfhglzfdg,
	look up the URI and perform the appropriate action on the
	user and neid.
	4) The UUIDs probably don't absolutely need to be persistent,
	so could use an in-memory cache. But then response handling
	would not survive a restart.
	5) If persistent, we need to clean the DB of old UUIDs
	periodically.
----------

TO DO (some complete - this is just a place to track
work-in-progress now):

) (done) Volunteers should be able to see and respond only to
events that are active and not already fully-staffed by
volunteers.

Story (DONE): Veronica the Volunteer logs into Unter.
(tested in test_volunteers.py)
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
  - Alerts contain response links that allow users to commit or
	decommit by clicking. Currently the format of those links
	is "/respond?user_id=U&neid=N". This is bad, those URLs are
	easily guessable. What we should actually do is generate a
	UUID for each user/event combination, store it associated
	with the event and user, and use it in the URL.
  - We also want users to be able to respond (or decommit) by
	responding to a text message. Need to check Twilio API
	for catching responses. ... OK, catching responses is
	easy. The difficult part is knowing which message the
	volunteer is responding to - we can't ask volunteers to
	include event IDs or UUIDs in their responses :-( That
	suggests we should send eg at most 1 alert per volunteer
	per hour, or something, so that we can be reasonably
	confident that when they respond "yes" we can assume they
	are responding to the last message we sent.
  * All of this will require a monitor process somewhere. Maybe just a
	cron job that pokes a URL on the web service every five
	minutes or something.

Story (TO BE WRITTEN)...

) Check that when a need event is created, volunteers who
are available at the time of the event and who are not
already committed to an event will receive an alert.

Story (DONE):
(test_need_events.py)
  - (done) Carla creates a need event for a family needing
    a ride to the airport on Sunday morning at 10:00 AM, which
    will take about 1 hour.
  - (done) Vincent, Veronica, and Velma are available at that time.
    However, Vincent has already committed to drive two
    individuals to the bus station at 10:15. 
  - (done) Veronica and Velma have not committed to any events that
    overlap the interval from 10:00 AM to 11:00 AM on Sunday 
    morning, so they should receive alerts. 
  - (done) Alerts are sent via email, and via text (if the volunteer
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
needed. That is, we want to be able to issue alerts not only
for new events, but for existing events that are not
yet claimed by volunteers.

Story (done): No volunteers have responded to Carla's Sunday
morning airport event as of Saturday morning. She goes
to the event page (which shows all active event) and:

  - (done) sees that an alert was last sent for that particular event
    on Friday morning.
  - (done) She can send a new alert for that event from the event list page,
    with a single click.
  - (done) She cannot send a new alert for events that have been
	alerted "recently" (within the last N hours, for come configurable
	value of N).
  - (done) Again, Veronica and Velma should recieve alerts.
  - (done) Carla should be able to click the event to see a list of 
    available volunteers for the event time, and their contact
    information.
  - (done) That list should include volunteers who have already committed
    to the event, clearly marked as having committed.

Story (INCOMPLETE): While looking at the event page, Carla notices
that there are some other events on Sunday and Monday
for which no volunteers have committed.

  - (done) She can issue alerts for all active and under-volunteered
    events with a single click from the event-list page.
  - (done) Alerts are sent only for events that have NOT had alerts sent
    within the past N hours, so Carla's airport event does
    NOT cause an additional alert to be generated (since
    she just sent an alert for that specific event, in
    the story above).
  - (done) NOTE: Show events in reverse temporal order on the event page.
  - Provide a "today's events only" link.
  - The "events for day" page should allow forward and backward navigation
	by day, and allow choosing a specific day.
  - CONSIDER: avoid alerting *volunteers* who have been alerted
    recently, to avoid event fatigue. (This would also allow us to
	disambiguate text replies to alerts more easily. If we only
	send one text per hour per volunteer, then it's pretty likely
    the one they're replying to is the last one we sent.)

) Allow coordinators manage volunteers.

Story (NOT STARTED):
	- A volunteer registers themself via the "Add volunteer" page.
    - They are NOT treated as a regular volunteer until a coordinator
	  approves them. This means:
      - They do not receive event alerts.
      - They cannot see the list of active events.
      - They cannot see any other users' information.
      - They CAN see and edit their own information,
		including available time periods.

Story (DONE):
	- A new person (Vespa) comes to Carla's site to volunteer.
    - Carla takes their information and uses the "add volunteer"
	  page to add Vespa to the volunteer DB.
    - Carla shows Vespa how to log in and manage her available times.
    - Vespa receives a confirmation email with a "login" link that
  	  takes her directly to the /login page.

Story (INCOMPLETE):
	- (done) Carla wants to know, in general, which volunteers are available.
    - (done) From her /coord_page, she can click a link to see a list of all
	  registered volunteers.
    - For each volunteer, she can see the number of events the
	  volunteer is available to serve and the number of events the
	  volunteer is committed to serve.
    - (done) She can click a row in the list of volunteers to see the
      volunteer_info page for the volunteer.

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

==========
Notes:

) If you add an attribute to model.User (in model/auth.py), it will
break test_auth.py unless you also add that attribute to the attrs dict
in tests/models/test_auth.py:TestUser
