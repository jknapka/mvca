'''
HACK: this is almost certainly not the best way to
handle this :-(

Work-around to allow i18n code to work both inside and
outside TG web requests.

The problem is that TG's implementations of ugettext and
lazy_ugettext work only inside web requests. So here we
check whether we are, in fact, inside a request, and if
not, we just return the untranslated string.
'''
import tg
from tg.i18n import ugettext, lazy_ugettext

__all__ = ["FAKE_","FAKEl_"]

def FAKE_(s):
    ''' Work around context issues. '''
    try:
        if tg.request:
            return ugettext(s)
    except TypeError:
        return s

def FAKEl_(s):
    ''' Work around context issues. '''
    try:
        if tg.request:
            return lazy_ugettext(s)
    except TypeError:
        return s


