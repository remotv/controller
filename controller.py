from __future__ import print_function

# TODO move all defs to the top of the file, out of the way of the flow of execution.
# TODO full python3 support will involve installing the adafruit drivers, not using the ones from the repo

import traceback
import argparse
import robot_util
import os.path
import networking
import time
import schedule
import sys
import watchdog
import logging
import logging.handlers
import json
import atexit

if (sys.version_info > (3, 0)):
    import importlib
    import _thread as thread
else:
    import thread
    # borrowed unregister function from
    # https://stackoverflow.com/questions/32097982/cannot-unregister-functions-from-atexit-in-python-2-7
    def unregister(func, *targs, **kargs):
        """unregister a function previously registered with atexit.
           use exactly the same aguments used for before register.
        """
        for i in range(0,len(atexit._exithandlers)):
            if (func, targs, kargs) == atexit._exithandlers[i] :
                del atexit._exithandlers[i]
                return True
        return False 
    atexit.unregister = unregister

from threading import Timer

# fail gracefully if configparser is not installed
try:
    from configparser import ConfigParser
    robot_config = ConfigParser()
except ImportError:
    print("Missing configparser module (python -m pip install configparser)")
    sys.exit()

try: 
    # Values in controller.conf will overwrite values in controller.sample.conf
    robot_config.read(['controller.sample.conf', 'controller.conf'])
except IOError:
    print("unable to read controller.conf, please check that you have copied controller.sample.conf to controller.conf and modified it appropriately.")
    sys.exit()
except:
    print ("Error in controller.conf:", sys.exc_info()[0])
    sys.exit()

def write(self, config_file):
    sections = 0
    keys = 0
    errors = 0
    keys_in = 0
    sections_in = 0

    # count sections and keys in config
    for section in self.sections():
        sections_in += 1
        for option in self[section]:
            keys_in += 1

    # read the existing config file
    with open(config_file, 'r') as fp:
        lines = fp.readlines()

    # parse the config file line by line and update any keys found
    for count, line in enumerate(lines):
        temp_line = line.lstrip(' \t')
        if temp_line[0] == '#' or temp_line[0] == ';':
            continue # comment
        elif temp_line[0] == '[':
            section = temp_line.find(']')
            if sections == -1:
                errors += 1
                log.error("ERROR: Unable parse line {} of config as [section] header : '{}'".format(count, line.rstrip('\r\n')))
            else:
                sections+=1
                section = temp_line[1:section]
        elif temp_line[0] == '\r' or temp_line[0] == '\n':
            continue # blank line
        else:
            key = temp_line.find('=')
            if key == -1:
                errors += 1
                log.error("ERROR: Unable parse line {} of config as key=value pair : '{}'".format(count, line.rstrip('\r\n')))
            else:
                keys += 1
                key = temp_line[0:key]
                key = key.strip()
                value = robot_config.get(section, key)
                lines[count] = '{}={}\n'.format(key, value)

    if sections != sections_in:
        log.error("ERROR: {} sections in file, {} in object".format(sections, sections_in))
    if keys != keys_in:
        log.error("ERROR: {} keys in file, {} in object".format(keys, keys_in))

    # delete the existing config backup
    if os.path.exists(config_file + '.bak'):
        os.remove(config_file + '.bak')

    os.rename(config_file, config_file+'.bak')

    # write out the updated config file
    f = open(config_file, 'w')
    f.writelines(lines)
    f.close

    log.info("Config file saved.")

ConfigParser.write = write

handlingCommand = False    
chat_module = None
move_handler = None

# pass the lock to robot_util so the controller can be terminated from outside.
terminate = thread.allocate_lock()
robot_util.terminate = terminate

# Enable logging, based upon the settings in the conf file.
log = logging.getLogger('RemoTV')
log.setLevel(logging.DEBUG)
console_handler=logging.StreamHandler()
console_handler.setLevel(logging.getLevelName(robot_config.get('logging', 'console_level')))
console_formatter=logging.Formatter('%(asctime)s - %(filename)s : %(message)s','%H:%M:%S')
console_handler.setFormatter(console_formatter)
try:
    file_handler=logging.handlers.RotatingFileHandler(robot_config.get('logging', 'log_file'),
        maxBytes=robot_config.getint('logging', 'max_size'),
        backupCount=robot_config.getint('logging', 'num_backup'))
except IOError:
    print("Error: Unable to write to log files. Check that they not owned by root, and that controller has write permissions to them")
    sys.exit()
            
file_handler.setLevel(logging.getLevelName(robot_config.get('logging', 'file_level')))
file_formatter=logging.Formatter('%(asctime)s %(name)s %(levelname)s - %(message)s','%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

log.addHandler(console_handler)
log.addHandler(file_handler)
log.critical('RemoTV Controller Starting up')

# Log all unhandled exceptions.
def exceptionLogger(exctype, value, tb):
    log.critical("Unhandled exception of type : {}".format(exctype),exc_info=(exctype, value, tb))
sys.excepthook = exceptionLogger

# This is required to allow us to get True / False boolean values from the
# command line    
def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')    

# TODO assess these and other options in the config to see which ones are most 
# appropriate to be overidden from the command line.
# check the command line for and config file overrides.
parser = argparse.ArgumentParser(description='start robot control program')
parser.add_argument('--robot-key', help='Robot API Key', default=robot_config.get('robot', 'robot_key'))
parser.add_argument('--type', help="Serial or motor_hat or gopigo2 or gopigo3 or l298n or motozero or pololu", default=robot_config.get('robot', 'type'))
parser.add_argument('--video', default=robot_config.get('camera', 'type'))
parser.add_argument('--custom-hardware', type=str2bool, default=robot_config.getboolean('misc', 'custom_hardware'))
parser.add_argument('--custom-tts', type=str2bool, default=robot_config.getboolean('misc', 'custom_tts'))
parser.add_argument('--custom-chat', type=str2bool, default=robot_config.getboolean('misc', 'custom_chat'))
parser.add_argument('--custom-video', type=str2bool, default=robot_config.getboolean('misc', 'custom_video'))
parser.add_argument('--ext-chat-command', type=str2bool, default=robot_config.getboolean('tts', 'ext_chat'))

parser.add_argument('--no-mic', dest='no_mic', action='store_true')
parser.set_defaults(no_mic=False)
parser.add_argument('--no-camera', dest='no_camera', action='store_true')
parser.set_defaults(no_camera=False)
parser.add_argument('--test', dest='test_mode', action='store_true')
parser.set_defaults(test_mode=False)
commandArgs = parser.parse_args()

log.debug('command line arguments : %s', commandArgs)

# push command line variables back into the config
robot_config.set('robot', 'robot_key', str(commandArgs.robot_key))
robot_config.set('robot', 'type', commandArgs.type)
robot_config.set('misc', 'custom_hardware', str(commandArgs.custom_hardware))
robot_config.set('misc', 'custom_tts', str(commandArgs.custom_tts))
robot_config.set('misc', 'custom_chat', str(commandArgs.custom_chat))
robot_config.set('tts', 'ext_chat', str(commandArgs.ext_chat_command))

if commandArgs.no_mic:
    robot_config.set('camera', 'no_mic', 'True')

if commandArgs.no_camera:
    robot_config.set('camera', 'no_camera', 'True')

# set variables pulled from the config
robotKey = commandArgs.robot_key
ext_chat = commandArgs.ext_chat_command
enable_async = robot_config.getboolean('misc', 'enable_async')

# check test_mode
test_mode = commandArgs.test_mode
if test_mode:
    log.critical("Remo.TV Controller starting in test mode")

if ext_chat:
    import extended_command


# Functions

def handle_message(ws, message):
    log.debug(message)

    try:
        messageData = json.loads(message)
    except:
        log.error("Unable to parse message")
        return

#    try:
    if "e" not in messageData:
        log.error("Malformed Message")
    event = messageData["e"]
    data = messageData["d"]

    if event == "BUTTON_COMMAND":
        on_handle_command(data)
       # handle_command(data)

    elif event == "MESSAGE_RECEIVED":
        if data['channel_id'] == networking.channel_id:
            if data['type'] != "robot":
               on_handle_chat_message(data)

    elif event == "ROBOT_VALIDATED":
        networking.handleConnectChatChannel(data["host"])

    else:
        log.error("Unknown event type")

#    except Exception as e:
#        print(e)

def handle_chat_message(args):
    log.info("chat message received: %s", args)

    if ext_chat:
        extended_command.handler(args)
            
    message = args["message"]

    try:
        if not message[0] == ".":
            tts.say(args)
    except IndexError:
        exit()
        
def handle_command(args):
        global handlingCommand
        handlingCommand = True

        # catch move commands that happen before the controller has fully
        # loaded and set a move handler.
        if move_handler == None:
           return

        log.debug('got command : %s', args)
        move_handler(args)

        handlingCommand = False
       

def on_handle_command(*args):
   log.debug("on_handle_command : {} {}".format(handlingCommand, enable_async))
   if handlingCommand and not enable_async:
       return
   else:
       thread.start_new_thread(handle_command, args)

def on_handle_chat_message(*args):
   if chat_module == None:
       thread.start_new_thread(handle_chat_message, args)
   else:
       thread.start_new_thread(chat_module.handle_chat, args)
   
def restart_controller(command, args):
    if extended_command.is_authed(args['sender']) == 2: # Owner
        terminate.acquire()

                    
# TODO : This really doesn't belong here, should probably be in start script.
# watch dog timer
if robot_config.getboolean('misc', 'watchdog'):
    import os
    os.system("sudo modprobe bcm2835_wdt")
    os.system("sudo /usr/sbin/service watchdog start")

# Load and start TTS
log.info("Loading tts")
import tts.tts as tts
tts.setup(robot_config)

# Connect to the networking sockets
if not test_mode:
   log.info("Loading networking")
   networking.setupWebSocket(robot_config, handle_message)

# If custom hardware extensions have been enabled, load them if they exist. Otherwise load the default
# controller for the specified hardware type.
log.info("Loading hardware module")
log.debug("Loading module hardware/%s", commandArgs.type)
if commandArgs.custom_hardware:
    if os.path.exists('hardware/hardware_custom.py'):
        if (sys.version_info > (3, 0)):
              module = importlib.import_module('hardware.hardware_custom')
        else:
            module = __import__('hardware.hardware_custom', fromlist=['hardware_custom'])
    else:
        log.warning("Unable to find hardware/hardware_custom.py")    
        if (sys.version_info > (3, 0)):
            module = importlib.import_module('hardware.'+commandArgs.type)
        else:
            module = __import__("hardware."+commandArgs.type, fromlist=[commandArgs.type])
else:
    if (sys.version_info > (3, 0)):
        module = importlib.import_module('hardware.'+commandArgs.type)
    else:
        module = __import__("hardware."+commandArgs.type, fromlist=[commandArgs.type])

#call the hardware module setup function
module.setup(robot_config)
move_handler = module.move

# Load the video handler
log.info("Loading video module")
log.debug("Loading module video/%s", commandArgs.video)
if commandArgs.custom_video:
    if os.path.exists('video/video_custom.py'):
        if (sys.version_info > (3, 0)):
            video_module = importlib.import_module('video.video_custom')
        else:
            video_module = __import__('video.video_custom', fromlist=['video_custom'])
    else:
        log.warning("Unable to find video/video_custom.py")    
        if (sys.version_info > (3, 0)):
            video_module = importlib.import_module('video.'+commandArgs.video)
        else:
            video_module = __import__("video."+commandArgs.video, fromlist=[commandArgs.video])
else:
    if (sys.version_info > (3, 0)):
        video_module = importlib.import_module('video.'+commandArgs.video)
    else:
        video_module = __import__("video."+commandArgs.video, fromlist=[commandArgs.video])

# Setup the video encoding
video_module.setup(robot_config)
if not test_mode:
   video_module.start()

#load the extended chat commands
if ext_chat:
    log.info("Loading extended chat commands")
    extended_command.setup(robot_config)
    extended_command.move_handler=move_handler
    move_handler = extended_command.move_auth
    extended_command.add_command('.restart', restart_controller)

# Load a custom chat handler if enabled and exists
if commandArgs.custom_chat:
    if os.path.exists('chat_custom.py'):
        if (sys.version_info > (3, 0)):
            chat_module = importlib.import_module('chat_custom')
        else:
            chat_module = __import__('chat_custom', fromlist=['chat_custom'])

        chat_module.setup(robot_config, handle_chat_message)
    
    else:
       log.warning("Unable to find chat_custom.py")
    
atexit.register(log.debug, "Attempting to clean up and exit nicely")
if not test_mode:
    log.critical('RemoTV Controller Started')
    while not terminate.locked():
        time.sleep(1)
        watchdog.watch()

    log.critical('RemoTV Controller Exiting')
else:
    log.critical('RemoTV Controller Test Complete')
sys.exit()
