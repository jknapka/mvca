'''
Test that need_events can be matched up with volunteers correctly.
'''
import unittest as ut
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import unter.model as model
from unter.websetup.bootstrap import create_entities
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt

class TestNeedEvent(ut.TestCase):
    '''
    Story:
      - Carla creates a need event for a family needing
        a ride to the airport on Sunday morning at 10:00 AM, which
        will take about 1 hour.
      - Vincent, Veronica, and Velma are available at that time.
        However, Vincent has already committed to drive two
        individuals to the bus station at 10:15. 
      - Veronica and Velma have not committed to any events that
        overlap the interval from 10:00 AM to 11:00 AM on Sunday 
        morning, so they should receive alerts. 
      - Alerts are sent via email, and via text (if the volunteer
        has indicated text alert preference).
      - Volunteer phone numbers are visible on the event
        page to logged-in coordinators, so they can make confirmation
        phone calls to volunteers.
      - Coordinator phone numbers are visible to volunteers for
        the events to which they have committed. Only the phone
        numbers for the coordinators who created those events
        are visible to volunteers, and only to the volunteers
        who commit to the events.
    '''

    def setUp(self):
        self.now = dt.datetime(2019,3,30,hour=12,minute=0)
        self.session = self.setupDB()

    def tearDown(self):
        self.session.close()

    def testCarlaExists(self):
        '''
        Check that Carla the coordinator exists.
        '''
        carla = self.session.query(model.User).filter_by(user_name='carla').first()
        self.assertTrue(carla is not None)

        carla2 = self.session.query(model.User).filter_by(user_name='carla2').first()
        self.assertTrue(carla2 is None)

    def testAirportNeedEvent_1(self):
        '''
        Check that we find the correct volunteers to alert for
        a given need event.
        '''
        nev = self.createAirportNeed(self.getUser(self.session,'carla'))

        volunteers = need.getAvailableVolunteers(self.session,nev)
        self.assertEqual(3,len(volunteers))
        names = [vol.user_name for vol in volunteers]
        self.assertTrue('vincent' in names)
        self.assertTrue('veronica' in names)
        self.assertTrue('velma' in names)

        volunteers = need.getUncommittedVolunteers(self.session,nev,volunteers)
        self.assertEqual(2,len(volunteers))
        names = [vol.user_name for vol in volunteers]
        self.assertTrue('veronica' in names)
        self.assertTrue('velma' in names)

    def testAirportNeedEvent_2(self):
        '''
        Check that getAlertableVolunteers() works as expected.
        '''
        nev = self.createAirportNeed(self.getUser(self.session,'carla'))

        volunteers = need.getAlertableVolunteers(self.session,nev)
        self.assertEqual(2,len(volunteers))
        names = [vol.user_name for vol in volunteers]
        self.assertTrue('veronica' in names)
        self.assertTrue('velma' in names)

    def testAlertAirportNeed(self):
        '''
        Check that alerts:
        1) Are sent when the event is new.
        2) Are not sent if the event was alerted within the past 4 hours.
        '''
        nev = self.createAirportNeed(self.getUser(self.session,'carla'))
        volunteers = need.getAlertableVolunteers(self.session,nev)

        # We should send alerts now, because the event is new.
        alertsSent = alerts.sendAlerts(volunteers,nev,honorLastAlertTime=True)
        self.assertTrue(alertsSent)

        # We should NOT send alerts now, because the event
        # was alerted recently.
        alertsSent = alerts.sendAlerts(volunteers,nev,honorLastAlertTime=True)
        self.assertFalse(alertsSent)

        # Back-date the alert time on nev so we can alert again.
        nev.last_alert_time = nev.last_alert_time - (3600*5)
        alertsSent = alerts.sendAlerts(volunteers,nev,honorLastAlertTime=True)
        self.assertTrue(alertsSent)

    def createAirportNeed(self,user):
        nev = model.NeedEvent()

        # March 31 2019 is a Sunday.
        nev.ev_type = model.NeedEvent.EV_TYPE_AIRPORT
        nev.date_of_need = dt.datetime(2019,3,31,12,0,0).timestamp()
        nev.time_of_need = 10*60
        nev.duration = 60
        nev.volunteer_count = 1
        nev.affected_persons = 2
        nev.location = 'Mesa Inn'
        nev.notes = 'Test - Veronica and Velma alert'
        nev.cancelled = 0
        nev.complete = 0
        nev.created_by = user

        self.session.add(nev)
        transaction.commit()

        return nev

    def setupDB(self):
        '''
        Set up the test DB.
        '''

        # Create the DB engine - this is the connection to the
        # back-end DB, which in this case is just an SQLite in-memory
        # one.
        engine = sql.create_engine('sqlite:///:memory:')

        # Create an ORM session bound to the engine.
        sessionmaker = orm.sessionmaker()
        session = sessionmaker(bind=engine)

        # Ensure that code that depends on model.DBSession uses
        # our session.
        model.DBSession = session

        # Create our model schema. This will create the schema for all
        # model classes we've imported.
        model.Group.metadata.create_all(engine)

        # Create the users and groups we need:

        # First the base TG bootstrap entities...
        create_entities(session)

        # Then the entities that support our test stories.
        g = session.query(model.Group).filter_by(group_name='coordinators').first()
        u = model.User(user_name='carla',display_name='Carla',email_address='carla@nowhere.com')
        g.users.append(u)
        session.flush()
        v = model.VolunteerInfo(user_id=u.user_id,zipcode='79900',phone='9150010001',
                description='Carla the coordinator')
        u.vinfo = v
        session.flush()
        transaction.commit()

        g = session.query(model.Group).filter_by(group_name='volunteers').first()
        phone = 9150010001
        for uname in ('Vincent','Veronica','Velma','Vernon','Vaughn'):
            phone += 1
            u = model.User(user_name=uname.lower(),display_name=uname,email_address=uname+'@nowhere.com')
            g.users.append(u)
            session.flush()
            v = model.VolunteerInfo(user_id=u.user_id,zipcode='79900',phone=str(phone),
                    description='{} the volunteer')
            u.vinfo = v
        transaction.commit()

        # Availabilities:
        
        # Vincent, Veronica and Velma available at 10:00 AM Sunday.
        av = model.VolunteerAvailability(start_time=9*60+15,end_time=12*60+45,
                dow_monday=0,
                dow_tuesday=0,
                dow_wednesday=0,
                dow_thursday=0,
                dow_friday=0,
                dow_saturday=0,
                dow_sunday=1)
        av.user = self.getUser(session,'vincent')
        session.add(av)
        transaction.commit()

        av = model.VolunteerAvailability(start_time=6*60,end_time=18*60,
                dow_monday=0,
                dow_tuesday=0,
                dow_wednesday=0,
                dow_thursday=0,
                dow_friday=1,
                dow_saturday=1,
                dow_sunday=1)
        av.user = self.getUser(session,'veronica')
        session.add(av)
        transaction.commit()

        av = model.VolunteerAvailability(start_time=9*60+15,end_time=12*60+45,
                dow_monday=1,
                dow_tuesday=0,
                dow_wednesday=0,
                dow_thursday=0,
                dow_friday=0,
                dow_saturday=0,
                dow_sunday=1)
        av.user = self.getUser(session,'velma')
        session.add(av)
        transaction.commit()

        av = model.VolunteerAvailability(start_time=9*60+15,end_time=12*60+45,
                dow_monday=1,
                dow_tuesday=0,
                dow_wednesday=0,
                dow_thursday=0,
                dow_friday=0,
                dow_saturday=0,
                dow_sunday=0)
        av.user = self.getUser(session,'velma')
        session.add(av)
        transaction.commit()

        av = model.VolunteerAvailability(start_time=9*60+15,end_time=12*60+45,
                dow_monday=0,
                dow_tuesday=0,
                dow_wednesday=0,
                dow_thursday=0,
                dow_friday=0,
                dow_saturday=1,
                dow_sunday=0)
        av.user = self.getUser(session,'vaughn')
        session.add(av)
        transaction.commit()

        # Need events: Vincent is committed to a bus-station
        # event.
        vne = model.NeedEvent()
        vne.ev_type = model.NeedEvent.EV_TYPE_BUS 
        vne.date_of_need = dt.datetime(2019,3,31).timestamp()
        vne.time_of_need = 60*10+15
        vne.duration = 65
        vne.volunteer_count = 1
        vne.affected_persons = 2
        vne.location = 'La Quinta West'
        vne.notes = 'Test - Vincent'
        vne.complete = 0
        vne.created_by = self.getUser(session,'carla')
        session.add(vne)

        transaction.commit()

        # Commit Vincent to the bus-station event.
        user = self.getUser(session,'vincent')
        vcom = model.VolunteerResponse()
        vcom.user = user
        vcom.need_event = vne
        session.add(vcom)

        transaction.commit()

        return session

    def getUser(self,session,uname):
        return session.query(model.User).filter_by(user_name=uname).first()

if __name__ == '__main__':
    ut.main()
