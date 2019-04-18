'''
Utilities for sending alerts.
'''
import datetime as dt
import logging
import importlib

from twilio.rest import Client as TwiCli

from unter.controllers.util import *

import tg

# Alert no more than every 4 hours for any particular event.
MIN_ALERT_SECONDS = 3600 * 4

SMS_ENABLED = True
EMAIL_ENABLED = True

# The base site URL to use in alerts.
MVCA_SITE = tg.config.get('mvca.site','https://127.0.0.1')

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
        logging.getLogger("unter").info("ALERTING {} for need event {}".format(vol.user_name,nev.neid))
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

#####################
# An SMS alerter that really sends an SMS, via Twilio.
#####################
TWILIO_SID = None
TWILIO_AUTH_TOK = None

def sendSMSUsingTwilio(message,sourceNumber="+19159743306",destNumber="+19155495098"):
    logging.getLogger('unter.alerts').info("Sending SMS alert to {} using Twilio.".format(destNumber))
    if TWILIO_SID is None:
        loadTwilioAuthData()
    if TWILIO_SID is None or TWILIO_AUTH_TOK is None:
        logging.getLogger('unter').error("Cannot send SMS via Twilio.")
        stubSMSAlerter(message,sourceNumber,destNumber)
        return
   
    cli = TwiCli(TWILIO_SID,TWILIO_AUTH_TOK)
    message = cli.messages.create(body=message,
            from_=sourceNumber,
            to=destNumber)
    print(message.sid)
    logging.getLogger('unter.alerts').info("   Message sent to {}".format(destNumber))

def loadTwilioAuthData():
    global TWILIO_SID,TWILIO_AUTH_TOK
    tw_sid_filename = tg.config.get('twilio.sid.filename')
    tw_auth_filename = tg.config.get('twilio.auth.filename')

    if tw_sid_filename is not None:
        with open(tw_sid_filename,'r') as inf:
            TWILIO_SID = inf.read().strip()
    else:
        logging.getLogger('unter').error("No twilio.sid.filename defined in [app:main]")

    if tw_auth_filename is not None:
        with open(tw_auth_filename,'r') as inf:
            TWILIO_AUTH_TOK = inf.read().strip()
    else:
        logging.getLogger('unter').error("No twilio.auth.filename defined in [app:main]")

#####################
# An SMS alerter that just logs the alert.
#####################
def stubSMSAlerter(message,sourceNumber="+10159743307",destNumber="+19155495098"):
    print("CALLING stubSMSAlerter({},{},{})".format(message,sourceNumber,destNumber))

#####################
# Alert settings.
#####################
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

#####################
# Configuration handler called from unter/config/app_config.py
# to configure SMS on app startup.
#####################
def configureSMSAlerts():
    '''
    Get the SMS alerter name from tg.config. Configure this
    in the [app:main] section of the .ini file, using
      sms.alerter = package.methodName
    eg
      sms.alerter = unter.controllers.alerts.sendSMSUsingTwilio
    '''
    smsAlerter = tg.config.get('sms.alerter')
    logging.getLogger('unter.alerts').info("SMS alerter sms.alerter = {}".format(smsAlerter))
    if smsAlerter is not None:
        try:
            pkg = '.'.join(smsAlerter.split('.')[:-1])
            method = smsAlerter.split('.')[-1]
            logging.getLogger('unter.alerts').info("  pkg {}, method {}".format(pkg,method))
            pkgModule = importlib.import_module(pkg)
            logging.getLogger('unter.alerts').info("  pkgModule {}".format(pkgModule))
            meth = pkgModule.__dict__[method]
            logging.getLogger('unter.alerts').info("  meth {}".format(meth))
            setSMSAlerter(meth)
        except:
            import sys
            logging.getLogger('unter.alerts').info("   meth deref exception: {}".format(sys.exc_info()))
    else:
        logging.getLogger('unter.alerts').info("No SMS alerter configured, using stub. Configure sms.alerter in .ini file.")
        setSMSAlerter(stubSMSAlerter)

__all__ = ["sendSMSUsingTwilio","stubSMSAlerter","getSMSAlerter","setSMSAlerter",
    "sendAlerts","SMS_ENABLED","EMAIL_ENABLED","MVCA_SITE","configureSMSAlerts"]

