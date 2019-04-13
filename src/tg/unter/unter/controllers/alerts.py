'''
Utilities for sending alerts.
'''
import datetime as dt

from twilio.rest import Client as TwiCli

from unter.controllers.util import *

# Alert no more than every 4 hours for any particular event.
MIN_ALERT_SECONDS = 3600 * 4

SMS_ENABLED = False
EMAIL_ENABLED = False

MVCA_SITE = "https://127.0.0.1"

def sendAlerts(volunteers,nev,honorLastAlertTime=True):
    '''
    Send alerts to the given volunteers for need event nev.
    '''
    if honorLastAlertTime:
        now = dt.datetime.now().timestamp()
        if now - MIN_ALERT_SECONDS < nev.last_alert_time:
            print("NOT alerting for need event {} - it was alerted recently.".format(\
                    nev.neid))
            return False
    for vol in volunteers:
        print("ALERTING {} for need event {}".format(vol.user_name,nev.neid))
        if SMS_ENABLED:
            if vol.vinfo.text_alerts_ok == 1:
                sendSmsForEvent(nev,vol)
        if EMAIL_ENABLED:
            sendEmailForEvent(nev,vol)
    nev.last_alert_time = int(dt.datetime.now().timestamp())
    return True

def sendEmailForEvent(nev,vol,source="MVCA"):
    '''
    Send an email using the configured EMAIL_ALERTER.
    '''
    print("FIX ME: implement email. Trying to send email to {} for neid {}".format(\
            vol.email_address,nev.neid))

def makeValidSMSPhoneNumber(num):
    if len(num) == 7:
        # Assume El Paso :-(
        num = "915"+num
    if num[:2] != "+1":
        num = "+1"+num
    return num

def sendSmsForEvent(nev,vol,source="MVCA"):
    '''
    Send an SMS alert for an event, using the configured
    SMS alerter. The SMS alerter can be configured using
    the setSMSAlerter() function. An SMS alerter is a
    function that takes a message, source phone number,
    and destination phone number.
    '''
    sendSMS = getSMSAlerter()

    destNumber = makeValidSMSPhoneNumber(vol.vinfo.phone)
    n_vols = nev.volunteer_count
    at_time=nev.time_of_need
    at_date=str(dt.date.fromtimestamp(nev.date_of_need))
    ev_type = nev.ev_type
    location = nev.location
    coord_num = nev.created_by.vinfo.phone
    coord_name = nev.created_by.display_name
    link = "{}/respond?user_id={}&neid={}".format(MVCA_SITE,vol.user_id,nev.neid)
    dlink = "{}/decommit?user_id={}&neid={}".format(MVCA_SITE,vol.user_id,nev.neid)
    msg = ("This is {}. We have a need for {} volunteer(s) at {} {}. Purpose: {}. "\
            +"Location: {}. Can you help? Call {} {} or click link to commit: {}. "\
            +"Or click to ignore: {}").format(source,\
            n_vols,\
            minutesPastMidnightToTimeString(at_time),\
            at_date,
            evTypeToString(ev_type),\
            location, coord_name, coord_num, link,dlink)
    sendSMS(msg,destNumber=destNumber)

# An SMS alerter that really sends an SMS, via Twilio.
def sendSMS(message,sourceNumber="+10159743307",destNumber="+19155495098"):
    sid = 'xxxx'
    auth_tok = 'xxxx'
   
    cli = TwiCli(sid,auth_tok)
    message = cli.messages.create(body=message,
            from_=sourceNumber,
            to=destNumber)
    print(message.sid)

# An SMS alerter that just logs the alert.
def stubSMSAlerter(message,sourceNumber="+10159743307",destNumber="+19155495098"):
    print("CALLING stubSMSAlerter({},{},{})".format(message,sourceNumber,destNumber))

SMS_ALERTER = stubSMSAlerter
EMAIL_ALERTER = sendEmailForEvent

# Get/set the SMS alert callable.
def getSMSAlerter():
    return SMS_ALERTER

def setSMSAlerter(alerter):
    global SMS_ALERTER
    SMS_ALERTER = alerter

# Get/set the email alert callable.
def getEmailAlerter():
    return EMAIL_ALERTER

def setEmailAlerter(alerter):
    global EMAIL_ALERTER
    EMAIL_ALERTER = alerter

__all__ = ["getSMSAlerter","setSMSAlerter","sendAlerts","SMS_ENABLED","EMAIL_ENABLED","MVCA_SITE"]

