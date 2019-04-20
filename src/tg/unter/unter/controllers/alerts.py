'''
Utilities for sending alerts.
'''
import datetime as dt
import logging
import importlib
import uuid

from twilio.rest import Client as TwiCli

from unter.controllers.util import *

import unter.model as model

import tg

__all__ = ["sendSMSUsingTwilio","stubSMSAlerter","getSMSAlerter","setSMSAlerter",
    "sendAlerts","SMS_ENABLED","EMAIL_ENABLED","MVCA_SITE","configureSMSAlerts"]

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
        logging.getLogger("unter.alerts").info("ALERTING {} for need event {}".format(vol.user_name,nev.neid))
        if SMS_ENABLED:
            if vol.vinfo.text_alerts_ok == 1:
                logging.getLogger('unter.alerts').info('  Alerting via SMS')
                sendSmsForEvent(nev,vol)
        if EMAIL_ENABLED:
            logging.getLogger('unter.alerts').info('  Alerting via email')
            sendEmailForEvent(nev,vol)
    nev.last_alert_time = int(dt.datetime.now().timestamp())
    return True

def sendEmailForEvent(nev,vol,source="MVCA"):
    '''
    Send an email using the configured EMAIL_ALERTER.
    '''
    emailAlerter = getEmailAlerter()
    toAddr = vol.email_address
    msg = makeMessageForEvent(nev,vol)
    emailAlerter(message=msg,toAddr=toAddr)

def stubEmailAlerter(message,toAddr,fromAddr="none@nowhere"):
    '''
    Default email alerter - merely logs an attempt to send email.
    '''
    logging.getLogger('unter.alerts').info("STUB email alert:\n  from: {}\n  to: {}\n{}".\
            format(fromAddr,toAddr,message))

SMTP_ALERTER = None
def sendEmailUsingSMTP(message,toAddr,fromAddr=None):
    '''
    An alerter that sends via a configured SMTP server.
    '''
    global SMTP_ALERTER
    if SMTP_ALERTER is None:
        SMTP_ALERTER = SMTPAlerter()
    SMTP_ALERTER.send_email(message,toAddr,fromAddr)

class SMTPAlerter:
    '''
    Send email using the configured SMTP account. The configuration
    options needed in the [app:main] section of the .ini file are:
    
    smtp.from = the from: address to use in outgoing messages.
    smtp.user.file = the file containing the SMTP user to log in as.
    smtp.pwd.file = the file containing the SMTP user's password.
    smtp.smtp.server = the name or IP of the SMTP SMTP server.

    Note that the credential files should NEVER be commited to
    version control.
    '''

    def __init__(self):
        self.ready = self.loadSMTPCredentials()

    def loadSMTPCredentials(self):
        '''
        Load the smtp login credentials. Return True if that
        succeeds, False otherwise.
        '''
        result = False
        userFname = tg.config.get('smtp.user.file',None)
        pwdFname = tg.config.get('smtp.pwd.file',None)
        
        if userFname is not None and pwdFname is not None:
            try:
                with open(userFname,'r') as inf:
                    self.user = inf.read().strip()
            except:
                logging.getLogger('unter.alerts').error("Could not load smtp user from file {}".format(userFname))
                return False
            try:
                with open(pwdFname,'r') as inf:
                    self.pwd = inf.read().strip()
            except:
                logging.getLogger('unter.alerts').error("Could not load smtp user from file {}".format(userFname))
                return False

        self.fromAddr = tg.config.get('smtp.from','mvca@mvca.org')
        self.smtpServer = tg.config.get('smtp.smtp.server','smtp.smtp.com:587')

        return True

    def send_email(message,toAddr,fromAddr=None):
        if not self.ready:
            logging.getLogger('unter.alerts').error('SMTP alerter not ready - not sending to {}'.format(toAddr))
            return
        if fromAddr is None:
            fromAddr = self.fromAddr

        # Credentials (if needed)
        username = self.user
        password = self.pwd
      
        # The actual mail send  
        server = smtplib.SMTP(self.smtpServer)
        server.ehlo()
        server.starttls()
        server.login(username,password)
        server.sendmail(fromAddr, toAddr, msg)
        server.quit()

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
    msg = makeMessageForEvent(nev,vol)
    sendSMS(msg,destNumber=destNumber)

def makeMessageForEvent(nev,vol,source='MVCA'):
    n_vols = nev.volunteer_count
    at_time=nev.time_of_need
    at_date=str(dt.date.fromtimestamp(nev.date_of_need))
    ev_type = nev.ev_type
    location = nev.location
    coord_num = nev.created_by.vinfo.phone
    coord_name = nev.created_by.display_name
    uuid = makeUUIDForAlert(nev,vol)
    link = "{}/sms_response?uuid={}&action=accept".format(MVCA_SITE,uuid)
    dlink = "{}/sms_response?uuid={}&action=refuse".format(MVCA_SITE,uuid)
    msg = ("This is {}. We have a need for {} volunteer(s) at {} {}. Purpose: {}. "\
            +"Location: {}. Can you help? Call {} {} or click link to commit: {}. "\
            +"Or click to ignore: {}").format(source,\
            n_vols,\
            minutesPastMidnightToTimeString(at_time),\
            at_date,
            evTypeToString(ev_type),\
            location, coord_name, coord_num, link,dlink)
    return msg

def makeUUIDForAlert(nev,vol):
    '''
    Create an entry in the AlertUUID table for the given
    event and volunteer.
    '''
    auuid = model.AlertUUID(user_id=vol.user_id,neid=nev.neid,uuid=str(uuid.uuid4()))
    result = auuid.uuid
    model.DBSession.add(auuid)
    model.DBSession.flush()
    return result

def getUserAndEventForUUID(uuid):
    '''
    Get the user and event associated with a UUID. Return the (user,event) tuple,
    or (None,None) if the UUID doesn't exist.
    '''
    result = None,None
    auuid = model.DBSession.query(model.AlertUUID).filter_by(uuid=uuid).first()
    if auuid is not None:
        result = auuid.user,auuid.need_event
        logging.getLogger('unter.alerts').info('Responding to alert UUID {} for user {} event {}'\
                .format(auuid.uuid,auuid.user.user_name,auuid.need_event.neid))
        # Don't delete. This allows the user to click on the
        # "decommit" link in the SMS to change their mind. We
        # should delete these when we vacuum old events out of
        # the DB.
        # model.DBSession.delete(auuid)
    else:
        logging.getLogger('unter.alerts').info('No such UUID {} for alert response.'.format(uuid))
    return result

#####################
# An SMS alerter that really sends an SMS, via Twilio.
# Note that we must configure a callable as the SMS alerter
# in the .ini file. That callable is sendSMSUsingTwilio(),
# below. It creates a TwilioSMSAlerter instance the first
# time it is called. (Do we need to make this thread-local?)
#####################
class TwilioSMSAlerter:

    def __init__(self):
        self.TWILIO_SID = None
        self.TWILIO_AUTH_TOK = None
        self.session = model.DBSession

        tw_sid_filename = tg.config.get('twilio.sid.filename')
        tw_auth_filename = tg.config.get('twilio.auth.filename')

        if tw_sid_filename is not None:
            with open(tw_sid_filename,'r') as inf:
                self.TWILIO_SID = inf.read().strip()
        else:
            logging.getLogger('unter').error("No twilio.sid.filename defined in [app:main]")

        if tw_auth_filename is not None:
            with open(tw_auth_filename,'r') as inf:
                self.TWILIO_AUTH_TOK = inf.read().strip()
        else:
            logging.getLogger('unter').error("No twilio.auth.filename defined in [app:main]")

    def __call__(self,message,sourceNumber=None,destNumber=None):
        logging.getLogger('unter.alerts').info("Sending SMS alert to {} using Twilio.".format(destNumber))
        if self.TWILIO_SID is None or self.TWILIO_AUTH_TOK is None:
            logging.getLogger('unter').error("Cannot send SMS via Twilio.")
            stubSMSAlerter(message,sourceNumber,destNumber)
            return
       
        try:
            cli = TwiCli(self.TWILIO_SID,self.TWILIO_AUTH_TOK)
            message = cli.messages.create(body=message,
                    from_=sourceNumber,
                    to=destNumber)
            print(message.sid)
            logging.getLogger('unter.alerts').info("   Message sent to {}".format(destNumber))
        except:
            logging.getLogger('unter.alerts').warn("   Message NOT sent to {}".format(destNumber))


TWILIO_SMS_ALERTER = None
def sendSMSUsingTwilio(message,sourceNumber="+19159743306",destNumber="+19155495098"):
    global TWILIO_SMS_ALERTER
    if TWILIO_SMS_ALERTER is None:
        TWILIO_SMS_ALERTER = TwilioSMSAlerter()
    TWILIO_SMS_ALERTER(message,sourceNumber,destNumber)

#####################
# An SMS alerter that just logs the alert.
#####################
def stubSMSAlerter(message,sourceNumber="+19159743306",destNumber="+19155495098"):
    logging.getLogger('unter.alerts').info("CALLING stubSMSAlerter({},{},{})".format(message,sourceNumber,destNumber))

#####################
# Alert settings.
#####################
SMS_ALERTER = stubSMSAlerter
EMAIL_ALERTER = stubEmailAlerter

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
    configHandler('sms.alerter',stubSMSAlerter,setSMSAlerter)

#####################
# Configuration handler called from unter/config/app_config.py
# to configure email on app startup.
#####################
def configureEmailAlerter():
    '''
    Get the email alerter name from tg.config. Configure
    this in the [app:main] section of the .ini file, using
      email.alerter = package.methodName
    eg
      email.alerter = unter.controllers.alerts.stubEmailAlerter
    '''
    configHandler('email.alerter',stubEmailAlerter,setEmailAlerter)

# Generic configuration handler.
def configHandler(alerterOpt,stubAlerter,assignmentLambda):
    alerter = tg.config.get(alerterOpt,None)
    logging.getLogger('unter.alerts').info("Alerter {} = {}".format(alerterOpt,alerter))
    if alerter is not None:
        try:
            pkg = '.'.join(alerter.split('.')[:-1])
            method = alerter.split('.')[-1]
            logging.getLogger('unter.alerts').info("  pkg {}, method {}".format(pkg,method))
            pkgModule = importlib.import_module(pkg)
            logging.getLogger('unter.alerts').info("  pkgModule {}".format(pkgModule))
            meth = pkgModule.__dict__[method]
            logging.getLogger('unter.alerts').info("  meth {}".format(meth))
            assignmentLambda(meth)
        except:
            import sys
            logging.getLogger('unter.alerts').info("   meth deref exception: {}".format(sys.exc_info()))
    else:
        logging.getLogger('unter.alerts').info("No alerter configured, using stub. Configure {} in .ini file.".format(alerterOpt))
        assignmentLambda(stubAlerter)

