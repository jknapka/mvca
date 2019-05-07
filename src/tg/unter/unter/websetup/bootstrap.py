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
    u.phone="9155495098"
    u.description = "Site manager"
    u.text_alerts_ok = 1
    u.zipcode = '79902'

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
    u1.phone="0000000000"
    u1.description = "Editor (unused)"
    u1.text_alerts_ok = 0
    u1.zipcode = '00000'

    session.add(u1)

    eTypes = [('Airport','Take people to the airport'),
            ('Bus Station','Take people to the bus station'),
            ('Interpreter','Provide interpreter services'),
            ('Serve Meal','Serve a meal to 50-200 people'),
            ('Prepare Meal','Prepare a meal for 50-200 people')
            ]

    for (name,desc) in eTypes:
        t = model.EventType()
        t.name = name
        t.description = desc
        session.add(t)

    transaction.commit()

    model.NeedEvent.EV_TYPE_AIRPORT = session.query(model.EventType).filter_by(name='Airport').first().etid
    model.NeedEvent.EV_TYPE_BUS = session.query(model.EventType).filter_by(name='Bus Station').first().etid
    model.NeedEvent.EV_TYPE_INTERPRETER = session.query(model.EventType).filter_by(name='Interpreter').first().etid

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
