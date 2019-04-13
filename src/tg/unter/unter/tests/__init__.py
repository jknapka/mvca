# -*- coding: utf-8 -*-
"""Unit and functional test suite for unter."""

from os import getcwd
from paste.deploy import loadapp
from webtest import TestApp
from gearbox.commands.setup_app import SetupAppCommand
from tg import config
from tg.util import Bunch

from unter import model

import datetime as dt

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

    def tearDown(self):
        """Tear down test fixture for each functional test method."""
        model.DBSession.remove()
        teardown_db()

    # Unter-specific utilities.
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
            date_of_need = dt.date.today() + dt.timedelta(days=1)
        vne = model.NeedEvent()
        vne.ev_type = ev_type
        vne.date_of_need = date_of_need.timestamp()
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
