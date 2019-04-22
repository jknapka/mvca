# -*- coding: utf-8 -*-
"""Unit and functional test suite for unter."""

from os import getcwd
import logging
from paste.deploy import loadapp
from webtest import TestApp
from gearbox.commands.setup_app import SetupAppCommand
from tg import config
from tg.util import Bunch

from unter import model

import datetime as dt
from io import StringIO

__all__ = ['setup_app', 'setup_db', 'teardown_db', 'TestController']

application_name = 'main_without_authn'


def load_app(name=application_name):
    """Load the test application."""
    return TestApp(loadapp('config:test.ini#%s' % name, relative_to=getcwd()))


def setup_app():
    """Setup the application."""
    cmd = SetupAppCommand(Bunch(options=Bunch(verbose_level=1)), Bunch())
    cmd.run(Bunch(config_file='config:test.ini', section_name=None))


def setup_db():
    """Create the database schema (not needed when you run setup_app)."""
    engine = config['tg.app_globals'].sa_engine
    model.init_model(engine)
    model.metadata.create_all(engine)


def teardown_db():
    """Destroy the database schema."""
    engine = config['tg.app_globals'].sa_engine
    model.metadata.drop_all(engine)


# Alerter stub that captures alert information for tests.
import unter.controllers.alerts as alerts
TEST_ALERT_OUTPUT = StringIO()

def setupSMSStub():
    global TEST_ALERT_OUTPUT
    logging.getLogger('unter.test').info('Setting up test SMS alerter. Use self.getAlertLog() to read alert data.')
    def stubSMSAlerter(msg,sourceNumber="+1SOURCE",destNumber="+1DEST"):
        print("('{}','{}','{}')".format(msg,sourceNumber,destNumber),file=TEST_ALERT_OUTPUT)
    alerts.setSMSAlerter(stubSMSAlerter)
    alerts.SMS_ENABLED = True
    TEST_ALERT_OUTPUT = StringIO()

# Email stub that captures email alert info for tests.
TEST_EMAIL_OUTPUT = StringIO()
def setupEmailStub():
    global TEST_EMAIL_OUTPUT
    logging.getLogger('unter.test').info('Setting up test email alerter. Use self.getEmailLog() to read alert data.')
    def testEmailAlerter(message,toAddr,fromAddr=None):
        print("Sending email:\n  to: {}\n  from: {}\n{}\nEND".format(toAddr,fromAddr,message),
                file=TEST_EMAIL_OUTPUT)
    alerts.setEmailAlerter(testEmailAlerter)
    alerts.EMAIL_ENABLED = True
    TEST_EMAIL_OUTPUT = StringIO()

class TestController(object):
    """Base functional test case for the controllers.

    The unter application instance (``self.app``) set up in this test
    case (and descendants) has authentication disabled, so that developers can
    test the protected areas independently of the :mod:`repoze.who` plugins
    used initially. This way, authentication can be tested once and separately.

    Check unter.tests.functional.test_authentication for the repoze.who
    integration tests.

    This is the officially supported way to test protected areas with
    repoze.who-testutil (http://code.gustavonarea.net/repoze.who-testutil/).

    """
    application_under_test = application_name

    def setUp(self):
        """Setup test fixture for each functional test method."""
        self.app = load_app(self.application_under_test)
        setup_app()

        # Override app config with test alerters.
        setupSMSStub()
        setupEmailStub()

    def tearDown(self):
        """Tear down test fixture for each functional test method."""
        model.DBSession.remove()
        teardown_db()

    # Unter-specific utilities.
    def getAlertLog(self):
        global TEST_ALERT_OUTPUT
        return TEST_ALERT_OUTPUT.getvalue()

    def resetAlertLog(self):
        global TEST_ALERT_OUTPUT
        TEST_ALERT_OUTPUT = StringIO()

    def getEmailLog(self):
        global TEST_EMAIL_OUTPUT
        return TEST_EMAIL_OUTPUT.getvalue()

    def resetEmailLog(self):
        global TEST_EMAIL_OUTPUT
        TEST_EMAIL_OUTPUT = StringIO()

    def createUser(self,user_name="test",email="test@test.test",
            phone="0010010001",desc="Test user",zipcode="79900",
            display_name=None,
            groups=[]):
        if display_name is None:
            display_name = user_name[0].upper()+user_name[1:] 
        u = model.User()
        u.user_name = user_name
        u.display_name = display_name
        u.email_address = email
        v = model.VolunteerInfo()
        v.phone = phone
        v.description = desc
        v.sipcode = zipcode
        u.vinfo = v

        for group in groups:
            g = model.DBSession.query(model.Group).filter_by(group_name=group).first()
            g.users.append(u)

        model.DBSession.add(u)
        return u

    def createAvailability(self,user,days=['m','t','w','th','f','s','su'],
            start_time=6*60+3,
            end_time=18*60+4):
        tf={True:1,False:0}
        if type(user) == str:
            user = self.getUser(model.DBSession,user)
        av = model.VolunteerAvailability(start_time=start_time,
                end_time=end_time,
                dow_monday=tf['m' in days],
                dow_tuesday=tf['t' in days],
                dow_wednesday=tf['w' in days],
                dow_thursday=tf['th' in days],
                dow_friday=tf['f' in days],
                dow_saturday=tf['s' in days],
                dow_sunday=tf['su' in days])
        av.user = user
        model.DBSession.add(av)
        return av

    def createEvent(self,created_by,
            ev_type=model.NeedEvent.EV_TYPE_BUS,
            date_of_need=None,
            time_of_need=10*60+19,
            duration=63,notes="DEFAULT NOTE",
            volunteer_count=1,
            affected_persons=2,
            location="Nowhere",
            complete=0):
        if date_of_need is None:
            date_of_need = dt.datetime.now() + dt.timedelta(days=1)
        vne = model.NeedEvent()
        vne.ev_type = ev_type
        vne.date_of_need = int(date_of_need.timestamp())
        vne.time_of_need = time_of_need
        vne.duration = duration
        vne.volunteer_count = volunteer_count
        vne.affected_persons = affected_persons
        vne.location = location
        vne.notes = notes
        vne.complete = complete
        vne.created_by = created_by
        model.DBSession.add(vne)
        return vne

    def createResponse(self,volName,evNotes):
        veronica = self.getUser(model.DBSession,volName)
        ev = model.DBSession.query(model.NeedEvent).filter_by(notes=evNotes).first()
        vr = model.VolunteerResponse()
        vr.user = veronica
        vr.need_event = ev
        model.DBSession.add(vr)

    def getUser(self,session,uname):
        return session.query(model.User).filter_by(user_name=uname).first()

    def setupNeedEventEntities(self):
        '''
        These are entities used in several user stories involving
        need event management.
        '''
        session = model.DBSession

        # Create the entities that support our test stories.
        # Users:
        u = self.createUser(user_name='carla',email='carla@nowhere.com',
                phone="9150010001",desc="Carla the coordinator",
                groups=["coordinators"])
        session.flush()

        phone = 9150010001
        for uname in ('Vincent','Veronica','Velma','Vernon','Vaughn'):
            phone += 1
            u = self.createUser(user_name=uname.lower(),display_name=uname,email=uname+'@nowhere.com',
                    phone=str(phone),
                    desc='{} the volunteer'.format(uname),
                    groups=["volunteers"])
            session.flush()

        # Availabilities:
        
        # Vincent, Veronica and Velma available at 10:00 AM Sunday.
        av =self.createAvailability(self.getUser(session,'vincent'),
                start_time=9*60+15,end_time=12*60+45,
                days=["su"])

        av = self.createAvailability(user=self.getUser(session,'veronica'),
                start_time=6*60,end_time=18*60,
                days=["f","s","su"])

        av = self.createAvailability(user=self.getUser(session,'velma'),
                start_time=9*60+15,end_time=12*60+45,
                days=["su","m"])

        av = self.createAvailability(user=self.getUser(session,'velma'),
                start_time=9*60+15,end_time=12*60+45,
                days=["m"])

        # Vaughn available only on Saturday.
        av = self.createAvailability(user=self.getUser(session,'vaughn'),
                start_time=9*60+15,end_time=12*60+45,
                days=["s"])

        # Need events: Vincent is committed to a bus-station
        # event.
        vne = self.createEvent(created_by=self.getUser(session,'carla'),
                date_of_need=dt.datetime(2019,3,31),
                time_of_need=60*10+15,
                duration=65,
                location="La Quinta West",
                notes='Test - Vincent')

        # Commit Vincent to the bus-station event.
        user = self.getUser(session,'vincent')
        vcom = model.VolunteerResponse()
        vcom.user = user
        vcom.need_event = vne
        session.add(vcom)

        return session

    def createVolunteers(self):
        veronica = self.createUser(user_name='veronica',email='v@mars.net',
                phone='9150010002',desc='Veronica the volunteer',
                groups=['volunteers'])
        
        velma = self.createUser(user_name='velma',email='velma@scooby.com',
                phone='9150010003',desc='Velma the volunteer',
                groups=['volunteers'])

        vaughn = self.createUser(user_name='vaughn',email='vaughn@nowhere.com',
                phone='9150010004',desc='Vaughn the volunteer',
                groups=['volunteers'])


    def createCoordinatorCarla(self):
        carla = self.createUser(user_name='carla',email='carla@nowhere.com',
                phone='9150010001',desc='Carla the coordinator',
                groups=['volunteers','coordinators'])

    def createAvailabilities(self):
        veronica = self.getUser(model.DBSession,'veronica')
        velma = self.getUser(model.DBSession,'velma')
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

    def createEvents(self):
        # Events:
        
        carla = self.getUser(model.DBSession,'carla')

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
