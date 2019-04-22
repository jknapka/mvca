'''
Test that coordinators receive alerts under appropriate conditions.
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

class TestCoordinatorAlerts(TestController):

    def setUp(self):
        super().setUp()

        self.createCoordinatorCarla()
        self.createVolunteers()

        # Create a test event.
        self.createEvent(created_by=self.getUser(model.DBSession,'carla'),
                location='test location',
                time_of_need=8*60)

        transaction.commit()


