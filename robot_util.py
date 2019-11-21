import requests
import time
import traceback
import ssl
import sys
import json
import logging
import networking

if (sys.version_info > (3, 0)):
    import urllib.request as urllib2
    from urllib.error import HTTPError
else:
    import urllib2
    from urllib2 import HTTPError

log = logging.getLogger('RemoTV.robot_util')

terminate=None

def terminate_controller():
    log.info('Attempting to terminate controller...')
    if terminate != None:
        # Changing this from terminate to sys.exit stops 
        # repeat_start from repeating start.
        
        #terminate.acquire()
        sys.exit()


# TODO : Think about rewriting this, and using request.

def getWithRetry(url, secure=True):
    for retryNumber in range(2000):
        try:
            log.debug("GET %s", url)
            if secure:
                response = urllib2.urlopen(url).read()
            else:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                response = urllib2.urlopen(url, context=ctx).read()
            break
        except:
            log.exception("could not open url %s", url)
            #traceback.print_exc()
            time.sleep(2)

    return response.decode('utf-8')

def sendChatMessage(message):
    networking.sendChatMessage(message)

