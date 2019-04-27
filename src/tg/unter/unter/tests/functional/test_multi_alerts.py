'''
Test that we send alerts only until an event is
fully-served. Check this for events that require
both single and multiple volunteers.

Test that volunteers who respond after
an event is fully-served receive a "No thanks" message.

Test that events that are fully-served don't have
"respond" links.
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

class TestMultiAlerts(TestController):

    def setUp(self):
        super().setUp()
        try:
            self.createVolunteers()
            self.createCoordinatorCarla()

            # Simple availabilities: one for velma and one
            # for veronica, 6AM to 6 PM each day.
            allDays = ['m','t','w','th','f','s','su']
            self.createAvailability(user='veronica',days=allDays,
                    start_time=60*6,end_time=60*18)
            self.createAvailability(user='velma',days=allDays,
                    start_time=60*6,end_time=60*18)

            cc = self.getUser(model.DBSession,'carla')

            # Two events that either volunteer can respond to:

            # One that requires a single volunteer:
            self.createEvent(created_by=cc, volunteer_count=1,
                    time_of_need=60*10,notes="event 1",location="location 1")

            # One that requires two volunteers:
            self.createEvent(created_by=cc, volunteer_count=2,
                    time_of_need=60*15,notes="event 2",location="location 2")

            # Ensure that email alerts are disabled. This simplifies
            # accounting of alert activity - we generate only one
            # alert UUID per event/volunteer, rather than two.
            alerts.EMAIL_ENABLED = False
            alerts.SMS_ENABLED = True

        except:
            import sys
            logging.getLogger('unter.test').error("ABORTING TRANSACTION in TestMultiAlerts: {}".format(sys.exc_info()))
            transaction.abort()
        else:
            transaction.commit()

    def sendAlert(self,ev_id):
        # Generate an alert.
        need.checkOneEvent(model.DBSession,ev_id=ev_id,honorLastAlertTime=False)
        transaction.commit()

    def test_0_oneVolunteerEvent(self):
        self.sendAlert(ev_id=1)

        # There should be 2 alert UUIDs.
        auuids = model.DBSession.query(model.AlertUUID).all()
        eq_(2,len(auuids),"Expected 2 alerts, saw {}".format(len(auuids)))

        # Let velma respond.
        self.createResponse('velma','event 1')

        self.sendAlert(ev_id=1)

        # This event is now fully-served, so there should still be
        # only 2 alerts UUIDs.
        auuids = model.DBSession.query(model.AlertUUID).all()
        eq_(2,len(auuids),"After response: Expected 2 alerts, saw {}".format(len(auuids)))

    def test_1_twoVolunteerEvent(self):
        self.sendAlert(ev_id=2)

        # There should be 2 alert UUIDs.
        auuids = model.DBSession.query(model.AlertUUID).all()
        eq_(2,len(auuids),"Expected 2 alerts, saw {}".format(len(auuids)))

        # Let velma respond.
        self.createResponse('velma','event 2')

        self.sendAlert(ev_id=2)

        # This event still requires one moe volunteer, so the last
        # alert should have alerted Veronica and there should now
        # be 3 alert UUIDs.
        auuids = model.DBSession.query(model.AlertUUID).all()
        eq_(3,len(auuids),"After response: Expected 3 alerts, saw {}".format(len(auuids)))

    def test_2_twoVolunteersRespondToOneVolEvent(self):
        ''' When 2 volunteers respond and only one is needed, the extra gets a "No thanks" alert.
            Also check that the first respondent gets a confirmation alert.
        '''
        env = {'REMOTE_USER':'velma'}
        self.app.get('/respond?neid=1',extra_environ=env)
        
        # There should be a single "Thank you for responding" alert.
        alerts = self.getAlertLog()
        ok_("Please go to location 1" in alerts,alerts)
        ok_("Enough volunteers have responded" not in alerts,alerts)

        self.resetAlertLog()
        env = {'REMOTE_USER':'veronica'}
        self.app.get('/respond?neid=1',extra_environ=env)

        # There should one alert for Veronica's "No more volunteers needed".
        alerts = self.getAlertLog()
        ok_("Enough volunteers have responded" in alerts,alerts)
        ok_("Please go to location 1" not in alerts,alerts)

    def test_3_oneVolunteerRespondsToTwoVolEvent(self):
        ''' When only one volunteer responds to an event needing two, others receive alerts.'''
        env = {'REMOTE_USER':'velma'}
        self.app.get('/respond?neid=2',extra_environ=env,status=302)

        # There should be a single "Thank you for responding" alert.
        alerts = self.getAlertLog()
        ok_("Please go to location 2" in alerts,alerts)
        ok_("Enough volunteers have responded" not in alerts,alerts)

        self.resetAlertLog()
        self.sendAlert(ev_id=2)

        # There should be one alert UUID.
        auuids = model.DBSession.query(model.AlertUUID).all()
        eq_(1,len(auuids),"Expected one alert UUID, found {}".format(len(auuids)))

        self.resetAlertLog()
        env = {'REMOTE_USER':'veronica'}
        self.app.get('/respond?neid=2',extra_environ=env,status=302)

        # There should be a single "Thank you for responding" alert.
        alerts = self.getAlertLog()
        ok_("Please go to location 2" in alerts,alerts)
        ok_("Enough volunteers have responded" not in alerts,alerts)

        self.resetAlertLog()
        self.sendAlert(ev_id=2)

        # There should still be only a single AUUID, since this event
        # is fully served and therefore no alerts were needed.
        auuids = model.DBSession.query(model.AlertUUID).all()
        eq_(1,len(auuids),"Expected one alert UUID, found {}".format(len(auuids)))


