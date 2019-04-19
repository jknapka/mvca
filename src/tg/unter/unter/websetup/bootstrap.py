# -*- coding: utf-8 -*-
"""Setup the unter application"""
from __future__ import print_function, unicode_literals
import transaction
from unter import model

def create_entities(session):
    u = model.User()
    u.user_name = 'manager'
    u.display_name = 'Site Manager'
    u.email_address = 'jaknapka+mvca.manager@gmail.com'
    u.password = 'managepass'

    vi = model.VolunteerInfo()
    vi.phone="9155495098"
    vi.description = "Site manager"
    vi.text_alerts_ok = 1
    vi.zipcode = '79902'
    u.vinfo = vi

    g = model.Group()
    g.group_name = 'managers'
    g.display_name = 'Managers Group'

    g.users.append(u)
    
    # Save for later.
    managers_group = g

    session.add(g)

    p = model.Permission()
    p.permission_name = 'manage'
    p.description = 'This permission gives an administrative right'
    p.groups.append(g)

    session.add(p)

    g = model.Group()
    g.group_name = 'volunteers'
    g.display_name = 'Volunteers Group'
    session.add(g)

    p = model.Permission(permission_name="respond_to_need",
            description="This permission allows a volunteer to respond to a need.")
    p.groups.append(g)
    session.add(p)

    g = model.Group()
    g.group_name = 'coordinators'
    g.display_name = 'Volunteer Coordinators Group'

    p = model.Permission()
    p.permission_name = 'manage_events'
    p.description = 'Permission to create and manage volunteer need events.'
    p.groups.append(g)
    p.groups.append(managers_group)

    session.add(p)
    session.add(g)
    session.add(u)

    u1 = model.User()
    u1.user_name = 'editor'
    u1.display_name = 'Example editor'
    u1.email_address = 'editor@somedomain.com'
    u1.password = 'editpass'

    session.add(u1)
    transaction.commit()

def bootstrap(command, conf, vars):
    """Place any commands to setup unter here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        create_entities(model.DBSession)
    except IntegrityError:
        print('Warning, there was a problem adding your auth data, '
              'it may have already been added:')
        import traceback
        print(traceback.format_exc())
        transaction.abort()
        print('Continuing with bootstrapping...')

    # <websetup.bootstrap.after.auth>
