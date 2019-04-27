'''
Test the "Add volunteer" page.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt

from tg import expose, flash, require, url, lurl

from unter.tests import TestController

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

from io import StringIO

import logging

class TestAddVolunteer(TestController):

    def test_0_anonymousCanLoadAddVolunteerPage(self):
        resp = self.app.get('/add_volunteer_start',status=200)
        ok_('User Name' in resp.text,resp.text)
        ok_('Display Name' in resp.text,resp.text)
