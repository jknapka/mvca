'''
Tests for the Unter application model classes.
'''
from __future__ import unicode_literals
from nose.tools import eq_,ok_

from unter import model
from unter.tests.models import ModelTest


class TestEventType(ModelTest):
    """Unit test case for the ``EventType`` model."""

    klass = model.EventType
    attrs = dict(
        name = 'Test Event Type',
        description = 'Test event type description'
    )

    def test_et_name(self):
        ''' EventType names are created properly. '''
        eq_('Test Event Type',self.obj.name)

    def test_et_description(self):
        ''' EventType descriptions are created properly. '''
        eq_('Test event type description',self.obj.description)

    def test_et_from_name(self):
        et = model.EventType.et_by_name('Test Event Type')
        ok_(et is not None,'Failed to find event by name')

    def test_et_from_id(self):
        et = model.EventType.et_by_id(1)
        ok_(et is not None,'Failed to find event by ID')
