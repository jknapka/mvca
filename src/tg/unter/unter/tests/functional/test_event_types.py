'''
Test that we can add and query event types.
'''
import sqlalchemy as sql
import sqlalchemy.orm as orm
import transaction
import unter.model as model
import unter.controllers.need as need
import unter.controllers.alerts as alerts
import datetime as dt

from unter.tests import TestController

from nose.tools import ok_, eq_

from bs4 import BeautifulSoup as bsoup

class TestNeedEvent(TestController):

    def setUp(self):
        super().setUp()
        self.createCoordinatorCarla()
        self.createVolunteers()
        transaction.commit()

    def test_0_addTypeLinkInAddEventPageForCoords(self):
        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/add_need_event_start',status=200,extra_environ=env)
        ok_('Add a new Type of Need' in resp.text,'Add-event-type link should be present for coordinators:\n{}'.\
                format(resp.text))

    def test_1_addTypeLinkAbsentForVols(self):
        env = {'REMOTE_USER':'veronica'}
        resp = self.app.get('/add_need_event_start',status=403,extra_environ=env)
        ok_('Add a new Type of Need' not in resp.text,'Add-event-type link should NOT be present for normal volunteers:\n{}'.\
                format(resp.text))

    def test_2_addEventTypePage(self):
        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/add_event_type_start',status=200,extra_environ=env)
        zup = bsoup(resp.text,features="html.parser")
        inps = zup.find_all('input')
        inms = [inp.get('name') for inp in inps]
        ok_('name' in inms,'No input named "name"')
        ok_('description' in inms,'No input named "description"')

    def test_3_canCreateEventType(self):
        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/add_event_type_post',status=302,extra_environ=env,
                params={'name':'TestEvent','description':'TestEvent description'})
        et = model.EventType.et_by_name('TestEvent')
        etNames = [e.name for e in model.DBSession.query(model.EventType).all()]
        ok_(et is not None,'Failed to create TestEvent: {}'.format(etNames))
        eq_('TestEvent description',et.description,'Wrong event description: {}'.format(et.description))

    def test_5_canCreateEventOfNewType(self):
        env = {'REMOTE_USER':'carla'}
        resp = self.app.get('/add_event_type_post',status=302,extra_environ=env,
                params={'name':'TestEvent','description':'TestEvent description'})
        et = model.EventType.et_by_name('TestEvent')
        ok_(et is not None,'Failed to create TestEvent')
        eq_('TestEvent description',et.description,'Wrong event description: {}'.format(et.description))
        
        resp = self.app.get('/add_need_event_start',status=200,extra_environ=env)
        ok_('TestEvent' in resp.text,'Did not find TestEvent in add-event form')

        et = model.EventType.et_by_name('TestEvent')
        etid = et.etid

        resp = self.app.post('/add_need_event_post',status=302,extra_environ=env,
                params=dict(\
                    date_of_need = '2100-01-01',\
                    time_of_need = '11:15',\
                    ev_type = "{}".format(etid),\
                    duration = 74,\
                    volunteer_count = 3,\
                    affected_persons = 40,\
                    location = "Somewhere",\
                    notes = "This is a test event"\
                    ))

        ev = model.DBSession.query(model.NeedEvent).filter_by(notes="This is a test event").first()
        ok_(ev is not None,'Failed to create need event')
        eq_('TestEvent description',ev.event_type.description,'Wrong event type: {}'.format(ev.event_type.description))
        eq_('Somewhere',ev.location)
        eq_(3,ev.volunteer_count)
        eq_(40,ev.affected_persons)
