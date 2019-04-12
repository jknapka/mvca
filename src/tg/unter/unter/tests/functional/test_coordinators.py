'''
Test the /coord_page URL.
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

class TestCoordPage(TestController):

    def setUp(self):
        super().setUp()
        try:
            self.setupDB()
        except:
            transaction.abort()
        else:
            transaction.commit()




    def setupDB(self):
        '''
        DB entities needed for these tests:

        1) A coordinator.
        2) A volunteer or two.
        3) Some events.
        4) At least one volunteer availability for an event.
        '''
        pass
