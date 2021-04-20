import sys
import robot_util
import json
import schedule
import tts.tts as tts
import watchdog
import logging
import random
import websocket
import os
import re
import robot_util
import schedule

if (sys.version_info > (3, 0)):
#    import _thread as thread
    import urllib.request as urllib2
else:
#    import thread
    import urllib2  #pylint: disable=import-error

log = logging.getLogger('RemoTV.networking')

robot_key = None
webSocket = None
server = None
version = None
channel = None
channel_id = None
chat = None
authenticated = False

internetStatus = True

no_chat_server = None

bootMessage = None

ipAddr = None

ood = None

def getChatChannels(host):
    url = 'https://%s/api/%s/channels/list/%s' % (server, version, host)
    response = robot_util.getWithRetry(url)
    log.debug("getChatChannels : %s", response)
    return json.loads(response)

def waitForWebSocket():
    while True:
        try:
            webSocket.run_forever()
        except AttributeError:
            log.warning("Warning: Web Socket not connected.")

def startListenForWebSocket():
    global webSocket

    watchdog.start("WebSocketListen", waitForWebSocket)

def onHandleWebSocketOpen(ws):
    ws.send(json.dumps({"e": "AUTHENTICATE_ROBOT", "d": {"token": robot_key}}))
    log.debug(json.dumps({"e": "AUTHENTICATE_ROBOT", "d": {"token": robot_key}}))
    log.info("websocket connected")

def onHandleWebSocketClose(ws):
    global authenticated
    authenticated = False
    log.info("websocket disconnect")

def onHandleWebSocketError(ws, error):
    log.error("WebSocket ERROR: {}".format(error))

def handleConnectChatChannel(host):
    global channel_id
    global chat
    global authenticated

    response = getChatChannels(host)
    log.debug(response)
    # Loop throught the return json and looked for the named channel, otherwise
    # use the first channel
    for key in response["channels"]:
        if key["name"] == channel:
            channel_id = key["id"]
            chat = key["chat"]
            log.info("channel {} found with id : {}".format(channel, channel_id))
            break

    if channel_id == None:
        channel_id = response["channels"][0]["id"]
        chat = response["channels"][0]["chat"]
        log.warning("channel {} NOT found, joining : {}".format(channel, channel_id))

    webSocket.send(json.dumps(
        {"e": "JOIN_CHANNEL", "d": channel_id}))
    webSocket.send(json.dumps(
        {"e": "GET_CHAT", "d": chat}))
    authenticated = True

def checkWebSocket():
    if not authenticated:
        log.critical("Websocket failed to connect or authenticate correctly")
        robot_util.terminate_controller()

def setupWebSocket(robot_config, onHandleMessage):
    global robot_key

    global bootMessage
    global webSocket
    global server
    global version
    global ipAddr
    global ood

    global channel

    robot_key = robot_config.get('robot', 'robot_key')
    server = robot_config.get('misc', 'server')

    if robot_config.has_option('misc', 'api_version'):
        version = robot_config.get('misc', 'api_version')
    else:
        version = 'dev'

    if robot_config.has_option('robot', 'channel'):
        channel = robot_config.get('robot', 'channel')

    bootMessages = robot_config.get('tts', 'boot_message')
    bootMessageList = bootMessages.split(',')
    bootMessage = random.choice(bootMessageList)

    if robot_config.has_option('tts', 'announce_ip'):
        ipAddr = robot_config.getboolean('tts', 'announce_ip')
    if ipAddr:
        addr = os.popen("ip -4 addr show wlan0 | grep -oP \'(?<=inet\\s)\\d+(\\.\\d+){3}\'").read().rstrip()
        log.info('IPv4 Addr : {}'.format(addr))
        bootMessage = bootMessage + ". My IP address is {}".format(addr)

    if robot_config.has_option('tts', 'announce_out_of_date'):
        ood = robot_config.getboolean('tts', 'announce_out_of_date')
    if ood:
        isOod = os.popen('git fetch && git status').read().rstrip()
        if "behind" in isOod:
            commits = re.search(r'\d+(\scommits|\scommit)', isOod)
            log.warning('Git repo is out of date. Run "git pull" to update.')
            bootMessage = bootMessage + ". Git repo is behind by {}.".format(commits.group(0))

#    log.info("using socket io to connect to control %s", controlHostPort)
    log.info("configuring web socket wss://%s/" % server)
    webSocket = websocket.WebSocketApp("wss://%s/" % server,
                                on_message=onHandleMessage,
                                on_error=onHandleWebSocketError,
                                on_open=onHandleWebSocketOpen,
                                on_close=onHandleWebSocketClose)
    log.info("staring websocket listen process")
    startListenForWebSocket()

    schedule.single_task(10, checkWebSocket)
    
    if robot_config.getboolean('misc', 'check_internet'):
        #schedule a task to check internet status
        schedule.task(robot_config.getint('misc', 'check_freq'), internetStatus_task)

def sendChatMessage(message):
    log.info("Sending Message : %s" % message)
    webSocket.send(json.dumps(
        {"e": "ROBOT_MESSAGE_SENT", 
         "d": {"message": "%s" % message,
               "chatId": "%s" % chat,
               "server_id": "%s" % server,
               "channel_id": "%s" % channel_id
        }
    }))

def isInternetConnected():
    try:
        url = 'https://{}'.format(server)
        urllib2.urlopen(url, timeout=1)
        log.debug("Server Detected")
        return True
    except urllib2.URLError as err:
        log.debug("Server NOT Detected {}".format(url))
        return False

lastInternetStatus = False

def internetStatus_task():
    global bootMessage
    global lastInternetStatus
    global internetStatus

    internetStatus = isInternetConnected()
    if internetStatus != lastInternetStatus:
        if internetStatus:
            tts.say(bootMessage)
            log.info("internet connected")
        else:
            log.info("missing internet connection")
            tts.say("missing internet connection")
    lastInternetStatus = internetStatus
