'''
Test alert UUID functionality.

When we send alert links, we want to avoid exposing user IDs
or event IDs in the response URLs. Therefore, we generate
hard-to-guess unique IDs for each user/event combination.
This test case checks that this mechanism works as expected.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import traceback
import datetime as dt
import re

import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts

from tg import expose, flash, require, url, lurl

from unter.tests import TestController

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

from io import StringIO

import logging

import unter.model as model
import unter.controllers.alerts as alerts
import unter.controllers.need as need

class TestAlertUUIDs(TestController):
    '''
    Test alert functionality.
    '''

    def setUp(self):
        super().setUp()
        try:
            self.createCoordinatorCarla()
            self.createVolunteers()
            self.createAvailabilities()
            self.createEvents()
        except:
            import sys
            logging.getLogger('unter.test').error("ABORTING TRANSACTION: {}".format(sys.exc_info()))
            transaction.abort()
        else:
            transaction.commit()

    def createAvailabilities(self):
        ''' Simplified vs super: only one availability for Veronica. '''
        self.createAvailability(user=self.getUser(model.DBSession,'veronica'),
                days=['m','t','w','th','f','s','su'],start_time=5*60,end_time=23*60)

    def createEvents(self):
        ''' Simplified vs super: only one event. '''
        self.ev = self.createEvent(created_by=self.getUser(model.DBSession,'carla'),
                date_of_need=dt.datetime.now()+dt.timedelta(days=1),
                time_of_need=10*60,notes="Test event")
        model.DBSession.flush()
        model.DBSession.expunge(self.ev) # Make this event valid after we commit.

    def sendAlert(self):
        # Call this only inside a transaction.
        model.DBSession.flush() # So we get a valid neid.
        need.checkOneEvent(model.DBSession,self.ev.neid,honorLastAlertTime=False)
        model.DBSession.flush()

    def test_0_alertsCreateUUIDs(self):
        ''' Check that sending an alert creates a UUID for the user and event. '''
        try:
            # We must manually manage transactions - no app context.
            self.sendAlert()
            uuids = model.DBSession.query(model.AlertUUID).all()
            eq_(len(uuids),1,"There should be only one alert UUID, for Veronica and event 1")
            auuid = uuids[0]
            eq_(auuid.user.user_name,'veronica','Alert UUID for wrong user {}'.format(auuid.user.user_name))
            eq_(auuid.neid,self.ev.neid,'Alert UUID for wrong event {} (expected {})'.format(auuid.neid,self.ev.neid))
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_0_alertsCreateUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

    def test_1_deleteEventDeletesUUIDs(self):
        ''' Check that deleting an event deletes associated UUID rows. '''
        try:
            model.DBSession.flush() # So we get a valid neid for self.ev.
            ev = model.DBSession.query(model.NeedEvent).filter_by(neid=self.ev.neid).first()
            ok_(ev is not None,"Event should exist.")
            need.checkOneEvent(model.DBSession,self.ev.neid)
            model.DBSession.flush()
            uuids = model.DBSession.query(model.AlertUUID).all()
            eq_(len(uuids),1,"There should be only one alert UUID, for Veronica and event 1")

            # Now delete the event.
            model.DBSession.delete(ev)
            model.DBSession.flush()
            ev = model.DBSession.query(model.NeedEvent).filter_by(neid=self.ev.neid).first()
            ok_(ev is None,"Event should no longer exist.")
            uuids = model.DBSession.query(model.AlertUUID).all()
            eq_(len(uuids),0,"Alert UUID should no longer exist.")
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_1_deleteEventDeletsUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

    def test_2_alertLinksUseUUIDs(self):
        ''' Check that alert texts contain UUIDs and not user or event IDs in URLs. '''
        try:
            self.sendAlert()
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_2_alertLinksUseUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
           transaction.commit()
        alerts = self.getAlertLog()
        auuid = model.DBSession.query(model.AlertUUID).first()
        ok_('uuid={}'.format(auuid.uuid) in alerts,"Missing UUID in alert log")
        ok_('user_id' not in alerts,"User ID should not be present in alert log.")
        ok_('neid' not in alerts,"Event ID should not be present in alert log.")

    def test_3_alertAcceptLinkCreatesResponse(self):
        ''' Check that an "accept" alert link creates a response row. '''
        try:
            self.sendAlert()
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_2_alertLinksUseUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

        # There should be no responses at this point.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),0,"VolunteerResponse objects exist.")

        alerts = self.getAlertLog()
        m = re.search('to commit: (http(s?)://.+&action=accept)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        acceptLink = m.groups()[0]
        eq_(acceptLink[:4],'http',acceptLink)
        eq_(acceptLink[-14:],"&action=accept",acceptLink)

        resp = self.app.get(acceptLink,status=200)

        # There should be one response now.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),1,"No VolunteerResponse objects exist.")

    def test_4_alertRefuseLinkCreatesDecommit(self):
        ''' Check that a "refuse" alert link creates a decommitment row. '''
        try:
            self.sendAlert()
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_2_alertLinksUseUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

        # There should be no responses at this point.
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),0,"VolunteerDecommitment objects exist.")

        alerts = self.getAlertLog()
        m = re.search('to ignore: (http(s?)://.+&action=refuse)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        decommitLink = m.groups()[0]
        eq_(decommitLink[:4],'http',decommitLink)
        eq_(decommitLink[-14:],"&action=refuse",decommitLink)

        resp = self.app.get(decommitLink,status=200)

        # There should be one response now.
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),1,"No VolunteerDecommitment objects exist.")

    def test_5_acceptLinksReusable(self):
        ''' Check that "accept" links in alerts can be safely triggered multiple times. '''
        try:
            self.sendAlert()
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_5_acceptLinksReusable(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

        # There should be no responses at this point.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),0,"VolunteerResponse objects exist.")

        alerts = self.getAlertLog()
        m = re.search('to commit: (http(s?)://.+&action=accept)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        acceptLink = m.groups()[0]
        eq_(acceptLink[:4],'http',acceptLink)
        eq_(acceptLink[-14:],"&action=accept",acceptLink)

        resp = self.app.get(acceptLink,status=200)

        # There should be one response now.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),1,"No VolunteerResponse objects exist.")

        resp = self.app.get(acceptLink,status=200)

        # There should still be only one response.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),1,"Wrong number of VolunteerResponse objects exist.")

    def test_6_refuseLinksResusable(self):
        ''' Check that a "refuse" alert link can be safely triggered multiple times.'''
        try:
            self.sendAlert()
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_2_alertLinksUseUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

        # There should be no responses at this point.
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),0,"VolunteerDecommitment objects exist.")

        alerts = self.getAlertLog()
        m = re.search('to ignore: (http(s?)://.+&action=refuse)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        decommitLink = m.groups()[0]
        eq_(decommitLink[:4],'http',decommitLink)
        eq_(decommitLink[-14:],"&action=refuse",decommitLink)

        resp = self.app.get(decommitLink,status=200)

        # There should be one response now.
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),1,"No VolunteerDecommitment objects exist.")

        resp = self.app.get(decommitLink,status=200)

        # There should still be only one response now.
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),1,"Wrong number of VolunteerDecommitment objects exist. Found {}, expected {}.".format(len(vresps),1))

    def test_7_usersCanChangeTheirMindsAfterAccepting(self):
        ''' Check that users can change their minds after accepting. '''
        try:
            self.sendAlert()
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_2_alertLinksUseUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

        # There should be no responses at this point.
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),0,"VolunteerDecommitment objects exist.")

        alerts = self.getAlertLog()

        # Get the links.
        m = re.search('to ignore: (http(s?)://.+&action=refuse)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        decommitLink = m.groups()[0]
        eq_(decommitLink[:4],'http',decommitLink)
        eq_(decommitLink[-14:],"&action=refuse",decommitLink)

        m = re.search('to commit: (http(s?)://.+&action=accept)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        acceptLink = m.groups()[0]
        eq_(acceptLink[:4],'http',acceptLink)
        eq_(acceptLink[-14:],"&action=accept",acceptLink)

        # Accept the event.
        resp = self.app.get(acceptLink,status=200)

        # There should be one response and no decommits.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),1,"Wrong number of VolunteerResponse objects exist {}.".format(len(vresps)))
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),0,"VolunteerDecommitment objects exist.")

        # Decommit from the event.
        resp = self.app.get(decommitLink,status=200)

        # There should be one decommit and no responses.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),0,"Wrong number of VolunteerResponse objects exist {}.".format(len(vresps)))
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),1,"Wrong number of VolunteerDecommitment objects exist {}.".format(len(vresps)))

    def test_8_usersCanChangeTheirMindsAfterRefusing(self):
        ''' Check that users can change their minds after refusing. '''
        try:
            self.sendAlert()
        except:
            transaction.abort()
            import sys
            sio = StringIO()
            traceback.print_tb(sys.exc_info()[2],file=sio)
            ok_(False,"ABORTED TRANSACTION in test_2_alertLinksUseUUIDs(): {}\n{}".format(sys.exc_info()[0],sio.getvalue()))
        else:
            transaction.commit()

        # There should be no responses at this point.
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),0,"VolunteerDecommitment objects exist.")

        alerts = self.getAlertLog()

        # Get the links.
        m = re.search('to ignore: (http(s?)://.+&action=refuse)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        decommitLink = m.groups()[0]
        eq_(decommitLink[:4],'http',decommitLink)
        eq_(decommitLink[-14:],"&action=refuse",decommitLink)

        m = re.search('to commit: (http(s?)://.+&action=accept)',alerts)
        ok_(m is not None,"No commit link in alert:\n{}".format(alerts))
        acceptLink = m.groups()[0]
        eq_(acceptLink[:4],'http',acceptLink)
        eq_(acceptLink[-14:],"&action=accept",acceptLink)

        # Decommit from the event.
        resp = self.app.get(decommitLink,status=200)

        # There should be one decommit and no responses.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),0,"Wrong number of VolunteerResponse objects exist {}.".format(len(vresps)))
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),1,"Wrong number of VolunteerDecommitment objects exist {}.".format(len(vresps)))

        # Accept the event.
        resp = self.app.get(acceptLink,status=200)

        # There should be one response and no decommits.
        vresps = model.DBSession.query(model.VolunteerResponse).all()
        eq_(len(vresps),1,"Wrong number of VolunteerResponse objects exist {}.".format(len(vresps)))
        vresps = model.DBSession.query(model.VolunteerDecommitment).all()
        eq_(len(vresps),0,"VolunteerDecommitment objects exist.")

