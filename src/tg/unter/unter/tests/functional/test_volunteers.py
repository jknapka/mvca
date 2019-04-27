'''
Test volunteer views and functionality.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt
import logging

from unter.tests import TestController

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

class TestVolunteers(TestController):

    '''
    Story: Veronica the Volunteer logs into Unter.
      - test_1 On her volunteer info page, she can see a list of events that
        occur during her times of availability.
      - test_1 She does not see events that do not occur during her
        times of availability.
      - test_2 She does not see events to which she has already committed in
        her available events list (she sees them in the committed events
        list).
      - test_3 She does not see events that overlap with events to which
        she has already committed.
      - test_4 She does not see events that are already being fully-served by
        other volunteers, even if she would be available for them.
      - test_5 She can click an link on an event row to confirm her ability to serve at
        the event.
      - test_6 She can click a different link to opt out of serving at the
        event, in which case she will recieve no further alerts about
        the event.
    '''

    def setUp(self):
        super().setUp()
        try:
            self.setupDB()
        except:
            import sys
            logging.error("ABORTING TRANSACTION: {}".format(sys.exc_info()))
            transaction.abort()
        else:
            transaction.commit()

    def test_0_fullyServed(self):
        '''
        We can tell when an event is fully-served by volunteers.
        '''
        try:
            # Velma responds.
            self.createResponse('velma','Veronica or Velma airport')
            ev = model.DBSession.query(model.NeedEvent).filter_by(notes="Veronica or Velma airport").first()
        except:
            import sys
            logging.error("ABORTING TRANSACTION: {}".format(sys.exc_info()))
            transaction.abort()
        else:
            transaction.commit()

        ev = model.DBSession.query(model.NeedEvent).filter_by(notes='Veronica or Velma airport').first()
        ok_(need.isFullyServed(model.DBSession,ev))


    def test_0_getAvailableEventsForVeronica(self):
        '''
        getAvailableEventsForVolunteer() gets Veronica's available events correctly.
        '''
        v = model.DBSession.query(model.User).filter_by(user_name='veronica').first()
        evs = need.getAvailableEventsForVolunteer(model.DBSession,v)
        eq_(4,len(evs),"Wrong number of available events {}".format(len(evs)))
        notes = [ev.notes for ev in evs]
        ok_('Veronica only bus 1' in notes)
        ok_('Veronica only airport' in notes)
        ok_('Veronica only bus 2' in notes)
        ok_('Veronica or Velma airport' in notes)
        ok_('Velma only bus' not in notes)

    def test_1_seeEventsAvailableToVeronica(self):
        '''
        Veronica can see the events she may be available to serve.
        '''
        environ = {'REMOTE_USER': 'veronica'}
        response = self.app.get('/volunteer_info',extra_environ=environ, status=200)
        ok_('Veronica' in response.text,"Missing user Veronica: "+response.text)
        ok_('Veronica only bus 1' in response.text,"Missing event: Veronica only bus 1: "+response.text)
        ok_('Veronica only bus 2' in response.text,"Missing event: Veronica only bus 2: "+response.text)
        ok_('Veronica only airport' in response.text,"Missing event: Veronica only airport: "+response.text)
        ok_("Veronica or Velma airport" in response.text,"Missing event: Veronica or Velma airport: "+response.text)
        ok_("Velma only bus" not in response.text,"Extra event: Velma only bus: "+response.text)

    def test_2_doNotSeeRespondedEvents(self):
        '''
        If Veronica responds to an event, she no longer sees that event as one she can respond to.
        '''
        # Veronica responds:
        # (Since we're not in app contest we must manage the txn.)
        try:
            self.createResponse('veronica','Veronica or Velma airport')
        except:
            transaction.abort()
        else:
            transaction.commit()

        environ = {'REMOTE_USER':'veronica'}
        response = self.app.get('/volunteer_info',extra_environ=environ,status=200)

        soup = bsoup(response.text,features="html.parser")
        availableDiv = soup.find(id="events-available")
        availableStr = str(availableDiv)
        ok_("Veronica or Velma airport" not in availableStr,"Unexpected event: Veronica or Velma airport"+availableStr)
        ok_('Veronica only bus 1' in response.text,"Missing event: Veronica only bus 1: "+availableStr)
        ok_('Veronica only bus 2' in response.text,"Missing event: Veronica only bus 2: "+availableStr)
        ok_('Veronica only airport' in response.text,"Missing event: Veronica only airport: "+availableStr)

    def test_3_doNotSeeOverlappingEvents(self):
        ''' Volunteers no longer see overlapping events as respondable.  '''
        # Veronica responds:
        # (Since we're not in app contest we must manage the txn.)
        try:
            self.createResponse('veronica','Veronica only bus 1')
        except:
            transaction.abort()
        else:
            transaction.commit()

        environ = {'REMOTE_USER':'veronica'}
        response = self.app.get('/volunteer_info',extra_environ=environ,status=200)

        soup = bsoup(response.text,features="html.parser")
        availableDiv = soup.find(id="events-available")
        availableStr = str(availableDiv)
        ok_("Veronica or Velma airport" in availableStr,"Missing event: Veronica or Velma airport"+availableStr)
        ok_('Veronica only bus 1' in response.text,"Missing event: Veronica only bus 1: "+availableStr)
        ok_('Veronica only airport' in response.text,"Missing event: Veronica only airport: "+availableStr)
        # We should NOT see the next one, it overlaps with the
        # bus event she responded to above.
        ok_('Veronica only bus 2' not in response.text,"Unexpected event: Veronica only bus 2: "+availableStr)

    def test_4_doNotSeeFullyServedEvents(self):
        ''' Volunteers do not see fully-served events as repsondable.  '''
        # Velma responds:
        # (Since we're not in app contest we must manage the txn.)
        try:
            self.createResponse('velma','Veronica or Velma airport')
        except:
            transaction.abort()
        else:
            transaction.commit()

        environ = {'REMOTE_USER':'veronica'}
        response = self.app.get('/volunteer_info',extra_environ=environ,status=200)

        soup = bsoup(response.text,features="html.parser")
        availableDiv = soup.find(id="events-available")
        availableStr = str(availableDiv)
        ok_("Veronica or Velma airport" not in availableStr,"Unexpected event: Veronica or Velma airport"+availableStr)
        ok_('Veronica only bus 1' in response.text,"Missing event: Veronica only bus 1: "+availableStr)
        ok_('Veronica only airport' in response.text,"Missing event: Veronica only airport: "+availableStr)
        ok_('Veronica only bus 2' in response.text,"Missing event: Veronica only bus 2: "+availableStr)

    def test_5_respondLinks(self):
        environ = {'REMOTE_USER':'veronica'}
        response = self.app.get('/volunteer_info',extra_environ=environ,status=200)
        soup = bsoup(response.text,features="html.parser")
        availableAnchors = soup.find(id="events-available").find_all("a")
        allAnchors = '\n'.join(map(str,availableAnchors))
        # We should see response links for neids 1,2,3 and 5.
        for id in [1,2,3,5]:
            ok_('"/respond?neid={}"'.format(id) in allAnchors)
        for id in [4]:
            ok_('"/respond?neid={}"'.format(id) not in allAnchors)

    def test_6_decommitLinks(self):
        try:
            self.createResponse('veronica','Veronica only airport')
            self.createResponse('veronica','Veronica or Velma airport')
        except:
            transaction.abort()
        else:
            transaction.commit()

        environ = {'REMOTE_USER':'veronica'}
        response = self.app.get('/volunteer_info',extra_environ=environ,status=200)
        soup = bsoup(response.text,features="html.parser")

        respondedAnchors = soup.find(id="events-responded").find_all("a")
        allAnchors = '\n'.join(map(str,respondedAnchors))
        # We should see decommit links for neids 2 and 5.
        for id in [2,5]:
            ok_('"/decommit?neid={}"'.format(id) in allAnchors)
        for id in [1,3,4]:
            ok_('"/decommit?neid={}"'.format(id) not in allAnchors)

        availableAnchors = soup.find(id="events-available").find_all("a")
        allAnchors = '\n'.join(map(str,availableAnchors))
        # We should see response links for neids 1 and 3.
        for id in [1,3]:
            ok_('"/respond?neid={}"'.format(id) in allAnchors)
        for id in [2,4,5]:
            ok_('"/respond?neid={}"'.format(id) not in allAnchors)


    def setupDB(self):
        veronica = self.createUser(user_name='veronica',email='v@mars.net',
                phone='9150010002',desc='Veronica the volunteer',
                groups=['volunteers'])
        
        velma = self.createUser(user_name='velma',email='velma@scooby.com',
                phone='9150020002',desc='Velma the volunteer',
                groups=['volunteers'])

        vaughn = self.createUser(user_name='vaughn',email='vaughn@nowhere.com',
                phone='9150030003',desc='Vaughn the volunteer',
                groups=['volunteers'])

        carla = self.createUser(user_name='carla',email='carla@nowhere.com',
                phone='9150010001',desc='Carla the coordinator',
                groups=['volunteers','coordinators'])

        # Veronica is available 10AM to 2PM on all days of the week.
        # (This saves us from having to create events on particular days
        # of the week.)
        av = self.createAvailability(user=veronica,
                start_time=10*60,end_time=14*60,
                days=["m","t","w","th","f","s","su"])

        # Velma is available noon to 3 on all days of the week.
        av = self.createAvailability(user=velma,
                start_time=12*60,end_time=15*60,
                days=["m","t","w","th","f","s","su"])

        # Events:

        # A bus and an airport for Veronica.
        self.createEvent(created_by=carla,
                ev_type=model.NeedEvent.EV_TYPE_BUS,
                date_of_need=dt.datetime.now() + dt.timedelta(days=1),
                time_of_need=10*60+30,
                location="Veronica only bus 1 location",
                notes="Veronica only bus 1")

        self.createEvent(created_by=carla,
                ev_type=model.NeedEvent.EV_TYPE_AIRPORT,
                date_of_need=dt.datetime.now() + dt.timedelta(days=2),
                time_of_need=10*60+33,
                location="Veronica only airport location",
                notes="Veronica only airport")

        # A bus that overlaps the other bus for Veronica:
        self.createEvent(created_by=carla,
                ev_type=model.NeedEvent.EV_TYPE_BUS,
                date_of_need=dt.datetime.now() + dt.timedelta(days=1),
                time_of_need=10*60+45,
                location="Veronica only bus 2 location",
                notes="Veronica only bus 2")

        # A bus for Velma.
        self.createEvent(created_by=carla,
                ev_type=model.NeedEvent.EV_TYPE_BUS,
                date_of_need=dt.datetime.now() + dt.timedelta(days=1),
                time_of_need=14*60+3,
                duration=20,
                location="Velma only bus location",
                notes="Velma only bus")

        # An airport that either Veronica or Velma could do.
        self.createEvent(created_by=carla,
                ev_type=model.NeedEvent.EV_TYPE_AIRPORT,
                date_of_need=dt.datetime.now() + dt.timedelta(days=1),
                time_of_need=12*60+23,
                location="Veronica or Velma airport location",
                notes="Veronica or Velma airport")
