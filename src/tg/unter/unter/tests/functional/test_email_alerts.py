'''
Test that email alerts produce the correct messages.
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

class TestEmailAlerts(TestController):
    '''
    Test emaal alert functionality.
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

        # Avoid creating UUIDs for SMSs.
        alerts.SMS_ENABLED = False

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

    def test_0_emailAlerts(self):
        try:
            self.sendAlert()
        except:
            import sys
            logging.getLogger('unter.test').error("ABORTING TRANSACTION in test_0_emailAlerts(): {}".\
                    format(sys.exc_info()))
            transaction.abort()
        else:
            transaction.commit()

        alerts = self.getEmailLog()
        ok_("to: v@mars.net" in alerts,alerts)

        auuids = model.DBSession.query(model.AlertUUID).all()
        eq_(len(auuids),1,"Wrong number of alerts sent: expected 1, found {}".format(len(auuids)))
