# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
from tg import expose, flash
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission
from tg import request, redirect, tmpl_context

from unter.lib.base import BaseController
import unter.model as model
from unter.controllers import util

__all__ = ['SecureController']


class SecureController(BaseController):
    """Sample controller-wide authorization"""

    # The predicate that must be met for all the actions in this controller:
    allow_only = has_permission(
        'manage',
        msg=l_('Only for people with the "manage" permission')
    )

    @expose('unter.templates.index')
    def index(self):
        """Let the user know that's visiting a protected controller."""
        flash(_("Secure Controller here"))
        return dict(page='index')

    @expose('unter.templates.index')
    def some_where(self):
        """Let the user know that this action is protected too."""
        return dict(page='some_where')

    #==================================
    # Utilities
    #==================================

    @expose()
    def testSetup(self):
        return '''
        <ul>
        <li><a href="/secc/setupTestUsers">Set up test users</a></li>
        <li><a href="/secc/setupTestAvailabilities">Set up test availabilities</a></li>
        <li><a href="/secc/setupTestEvents">Set up test events</a></li>
        </ul>
        '''

    @expose()
    def setupTestUsers(self):
        util.setupTestUsers()
        redirect("/secc/testSetup")

    @expose()
    def setupTestAvailabilities(self):
        util.setupTestAvailabilities()
        redirect("/secc/testSetup")

    @expose()
    def setupTestEvents(self):
        util.setupTestEvents()
        redirect("/secc/testSetup")

