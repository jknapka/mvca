'''
Test that managers can promote volunteers.
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

class TestPromotions(TestController):

    def setUp(self):
        super().setUp()
        try:
            self.createCoordinatorCarla()
            self.createVolunteers()
        except:
            import sys
            logging.getLogger('unter.test').error("ABORTING TRANSACTION: {}".format(sys.exc_info()))
        else:
            transaction.commit()

    def test_0_managersHavePromotionLinks(self):
        ''' Promotion links appear in the "manager" view of volunteer_info. '''
        resp = self.app.get("/add_volunteer_start?user_id=6",
                extra_environ={'REMOTE_USER':'manager'},
                status=200)
        ok_('Promote volunteer to coordinator' in resp.text,resp.text)
        ok_('Promote volunteer to manager' in resp.text,resp.text)

    def test_1_noPromotionLinksForCoords(self):
        ''' Promotion links DO NOT appear in the "coordinator" view of volunteer_info. '''
        resp = self.app.get("/add_volunteer_start?user_id=6",
                extra_environ={'REMOTE_USER':'carla'},
                status=200)
        ok_('Promote volunteer to coordinator' not in resp.text,resp.text)
        ok_('Promote volunteer to manager' not in resp.text,resp.text)

    def test_2_noPromotionLinksForVolunteers(self):
        ''' Promotion links DO NOT appear in the "volunteer" view of volunteer_info. '''
        u = model.DBSession.query(model.User).filter_by(user_id=6).first()
        user_name = u.user_name
        resp = self.app.get("/add_volunteer_start?user_id=6",
                extra_environ={'REMOTE_USER':user_name},
                status=200)
        ok_('Promote volunteer to coordinator' not in resp.text,resp.text)
        ok_('Promote volunteer to manager' not in resp.text,resp.text)

    def test_3_promotionToCoord(self):
        ''' Promotion to coordinator works. '''
        u = model.DBSession.query(model.User).filter_by(user_id=6).first()
        ok_('manage_events' not in [p.permission_name for p in u.permissions],u.permissions)
        resp = self.app.get("/promote_to_coordinator?user_id=6",
                extra_environ={'REMOTE_USER':'manager'},
                status=302)
        u = model.DBSession.query(model.User).filter_by(user_id=6).first()
        ok_('manage_events' in [p.permission_name for p in u.permissions],u.permissions)

    def test_4_promotionToManager(self):
        ''' Promotion to manager works. '''
        u = model.DBSession.query(model.User).filter_by(user_id=6).first()
        ok_('manage' not in [p.permission_name for p in u.permissions],u.permissions)
        resp = self.app.get("/promote_to_manager?user_id=6",
                extra_environ={'REMOTE_USER':'manager'},
                status=302)
        u = model.DBSession.query(model.User).filter_by(user_id=6).first()
        ok_('manage' in [p.permission_name for p in u.permissions],u.permissions)

    def test_5_noPromoteToCoordLinkForCoords(self):
        ''' When viewing a coordinator there is no "Promote to coord" link. '''
        resp = self.app.get('/add_volunteer_start?user_id=3',
                extra_environ={'REMOTE_USER':'manager'},
                status=200)
        ok_('Promote volunteer to coordinator' not in resp.text,resp.text)
        ok_('Promote volunteer to manager' in resp.text,resp.text)

    def test_6_noPromoteToManagerLinkForManagers(self):
        ''' When viewing a manager there is no "Promote to manager" link. '''
        resp = self.app.get('/add_volunteer_start?user_id=1',
                extra_environ={'REMOTE_USER':'manager'},
                status=200)
        # Note: user 'manager' is also a coordinator.
        ok_('Promote volunteer to coordinator' not in resp.text,resp.text)
        ok_('Promote volunteer to manager' not in resp.text,resp.text)

    def test_7_unpromoteCoord(self):
        ''' Test that we can remove Carla the Coordinator's coord privilege. '''
        resp = self.app.get('/unpromote?user_id=3',
                extra_environ={'REMOTE_USER':'manager'},
                status=302)
        u = model.DBSession.query(model.User).filter_by(user_id=3).first()
        eq_('carla',u.user_name,u.user_name)
        ok_('manage_events' not in [p.permission_name for p in u.permissions],u.permissions)

    def test_8_unpromoteManager(self):
        ''' Test that we can promote Carla to manager, then remove her admin privileges. '''
        u = model.DBSession.query(model.User).filter_by(user_id=3).first()
        ok_('manage' not in [p.permission_name for p in u.permissions],u.permissions)
        resp = self.app.get("/promote_to_manager?user_id=3",
                extra_environ={'REMOTE_USER':'manager'},
                status=302)
        u = model.DBSession.query(model.User).filter_by(user_id=3).first()
        ok_('manage' in [p.permission_name for p in u.permissions],u.permissions)

        resp = self.app.get('/unpromote?user_id=3',
                extra_environ={'REMOTE_USER':'manager'},
                status=302)
        u = model.DBSession.query(model.User).filter_by(user_id=3).first()
        eq_('carla',u.user_name,u.user_name)
        ok_('manage_events' not in [p.permission_name for p in u.permissions],u.permissions)
        ok_('manage' not in [p.permission_name for p in u.permissions],u.permissions)
