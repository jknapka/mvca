# -*- coding: utf-8 -*-
"""Setup the unter application"""
from __future__ import print_function, unicode_literals
import transaction
from unter import model


def bootstrap(command, conf, vars):
    """Place any commands to setup unter here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        u = model.User()
        u.user_name = 'manager'
        u.display_name = 'Example manager'
        u.email_address = 'manager@somedomain.com'
        u.password = 'managepass'

        g = model.Group()
        g.group_name = 'managers'
        g.display_name = 'Managers Group'

        g.users.append(u)

        model.DBSession.add(g)

        p = model.Permission()
        p.permission_name = 'manage'
        p.description = 'This permission gives an administrative right'
        p.groups.append(g)

        model.DBSession.add(p)

        g = model.Group()
        g.group_name = 'volunteers'
        g.display_name = 'Volunteers Group'
        model.DBSession.add(g)

        p = model.Permission(permission_name="respond_to_need",
                description="This permission allows a volunteer to respond to a need.")
        p.groups.append(g)
        model.DBSession.add(p)

        g = model.Group()
        g.group_name = 'coordinators'
        g.display_name = 'Volunteer Coordinators Group'

        p = model.Permission()
        p.permission_name = 'manage_events'
        p.description = 'Permission to create and manage volunteer need events.'
        p.groups.append(g)

        model.DBSession.add(p)
        #g.users.append(u)
        model.DBSession.add(g)
        model.DBSession.add(u)

        u1 = model.User()
        u1.user_name = 'editor'
        u1.display_name = 'Example editor'
        u1.email_address = 'editor@somedomain.com'
        u1.password = 'editpass'

        model.DBSession.add(u1)
        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print('Warning, there was a problem adding your auth data, '
              'it may have already been added:')
        import traceback
        print(traceback.format_exc())
        transaction.abort()
        print('Continuing with bootstrapping...')

    # <websetup.bootstrap.after.auth>
