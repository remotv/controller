# This is a dummy file to allow the automatic loading of modules without error on none.
import anki_vector
import atexit
import time
import _thread as thread
import logging
import networking

log = logging.getLogger('RemoTV.vector')
vector = None
reserve_control = None
robotKey = None

annotated = False

def connect():
    global vector
    global reserve_control

    log.debug("Connecting to Vector")
    vector = anki_vector.AsyncRobot()
    vector.connect()
    #reserve_control = anki_vector.behavior.ReserveBehaviorControl()
    
    atexit.register(exit)

    return(vector)

def exit():
    log.debug("Vector exiting")
    vector.disconnect()
    
def setup(robot_config):
    global forward_speed
    global turn_speed
    global volume
    global vector
    global charge_high
    global charge_low
    global stay_on_dock

    global robotKey
    global server
    global no_mic
    global no_camera
    global ffmpeg_location
    global v4l2_ctl_location
    global x_res
    global y_res
    
    robotKey = robot_config.get('robot', 'robot_key')

    if robot_config.has_option('misc', 'video_server'):
        server = robot_config.get('misc', 'video_server')
    else:
        server = robot_config.get('misc', 'server')
 
    no_mic = robot_config.getboolean('camera', 'no_mic')
    no_camera = robot_config.getboolean('camera', 'no_camera')

    ffmpeg_location = robot_config.get('ffmpeg', 'ffmpeg_location')
    v4l2_ctl_location = robot_config.get('ffmpeg', 'v4l2-ctl_location')

    x_res = robot_config.getint('camera', 'x_res')
    y_res = robot_config.getint('camera', 'y_res')


    if vector == None:
        vector == connect()

    #x  mod_utils.repeat_task(30, check_battery, coz)

    if robot_config.has_section('cozmo'):
        forward_speed = robot_config.getint('cozmo', 'forward_speed')
        turn_speed = robot_config.getint('cozmo', 'turn_speed')
        volume = robot_config.getint('cozmo', 'volume')
        charge_high = robot_config.getfloat('cozmo', 'charge_high')
        charge_low = robot_config.getfloat('cozmo', 'charge_low')
        stay_on_dock = robot_config.getboolean('cozmo', 'stay_on_dock')

#    if robot_config.getboolean('tts', 'ext_chat'): #ext_chat enabled, add motor commands
#        extended_command.add_command('.anim', play_anim)
#        extended_command.add_command('.forward_speed', set_forward_speed)
#        extended_command.add_command('.turn_speed', set_turn_speed)
#        extended_command.add_command('.vol', set_volume)
#        extended_command.add_command('.charge', set_charging)
#        extended_command.add_command('.stay', set_stay_on_dock)

    vector.audio.set_master_volume(volume) # set volume

    return
    
def move(args):
    global charging
    global low_battery
    command = args['button']['command']

    try:
        if vector.status.is_on_charger and not charging:
            if low_battery:
                print("Started Charging")
                charging = 1
            else:
                if not stay_on_dock:
                    coz.drive_off_charger_contacts().wait_for_completed()

        if command == 'f':
            vector.behavior.say_text("Moving {}".format(command))

            #causes delays #coz.drive_straight(distance_mm(10), speed_mmps(50), False, True).wait_for_completed()
            vector.motors.set_wheel_motors(forward_speed, forward_speed, forward_speed*4, forward_speed*4 )
            time.sleep(0.7)
            vector.motors.set_wheel_motors(0, 0)
        elif command == 'b':
            #causes delays #coz.drive_straight(distance_mm(-10), speed_mmps(50), False, True).wait_for_completed()
            vector.motors.set_wheel_motors(-forward_speed, -forward_speed, -forward_speed*4, -forward_speed*4 )
            time.sleep(0.7)
            vector.motors.set_wheel_motors(0, 0)
        elif command == 'l':
            #causes delays #coz.turn_in_place(degrees(15), False).wait_for_completed()
            vector.motors.set_wheel_motors(-turn_speed, turn_speed, -turn_speed*4, turn_speed*4 )
            time.sleep(0.5)
            vector.motors.set_wheel_motors(0, 0)
        elif command == 'r':
            #causes delays #coz.turn_in_place(degrees(-15), False).wait_for_completed()
            vector.motors.set_wheel_motors(turn_speed, -turn_speed, turn_speed*4, -turn_speed*4 )
            time.sleep(0.5)
            vector.motors.set_wheel_motors(0, 0)

        #move lift
        elif command == 'w':
            vector.behavior.say_text("w")
            vector.set_lift_height(height=1).wait_for_completed()
        elif command == 's':
            vector.behavior.say_text("s")
            vector.set_lift_height(height=0).wait_for_completed()

        #look up down
        #-25 (down) to 44.5 degrees (up)
        elif command == 'q':
            #head_angle_action = coz.set_head_angle(degrees(0))
            #clamped_head_angle = head_angle_action.angle.degrees
            #head_angle_action.wait_for_completed()
            vector.behaviour.set_head_angle(45)
            time.sleep(0.35)
            vector.behaviour.set_head_angle(0)
        elif command == 'a':
            #head_angle_action = coz.set_head_angle(degrees(44.5))
            #clamped_head_angle = head_angle_action.angle.degrees
            #head_angle_action.wait_for_completed()
            vector.behaviour.set_head_angle(-22.0)
            time.sleep(0.35)
            vector.behaviour.set_head_angle(0)
   
        #things to say with TTS disabled
        elif command == 'sayhi':
            tts.say( "hi! I'm cozmo!" )
        elif command == 'saywatch':
            tts.say( "watch this" )
        elif command == 'saylove':
            tts.say( "i love you" )
        elif command == 'saybye':
            tts.say( "bye" )
        elif command == 'sayhappy':
            tts.say( "I'm happy" )
        elif command == 'saysad':
            tts.say( "I'm sad" )
        elif command == 'sayhowru':
            tts.say( "how are you?" )
    except:
        return(False)
    return

def start():
    log.debug("Starting Vector Video Process")
    try:
        thread.start_new_thread(video, ())
    except KeyboardInterrupt as e:
        pass        
    return
    
def video():
    # Turn on image receiving by the camera
    vector.camera.init_camera_feed()

    vector.behavior.say_text("hey everyone, lets robot!")

    while True:
        time.sleep(0.25)

        from subprocess import Popen, PIPE
        from sys import platform

        log.debug("ffmpeg location : {}".format(ffmpeg_location))

#        import os
#        if not os.path.isfile(ffmpeg_location):
#        print("Error: cannot find " + str(ffmpeg_location) + " check ffmpeg is installed. Terminating controller")
#        thread.interrupt_main()
#        thread.exit()

        while not networking.authenticated:
            time.sleep(1)


        p = Popen([ffmpeg_location, '-y', '-f', 'image2pipe', '-vcodec', 'png', '-r', '25', '-i', '-', '-vcodec', 'mpeg1video', '-r', '25', "-f", "mpegts", "-headers", "\"Authorization: Bearer {}\"".format(robotKey), "http://{}:1567/transmit?name={}-video".format(server, networking.channel_id)], stdin=PIPE)
       
        try:
            while True:
                if vector:
                    image = vector.camera.latest_image
                    if image:
                        if annotated:
                            image = image.annotate_image()
                        else:
                            image = image.raw_image
                        image.save(p.stdin, 'PNG')
                else:
                    time.sleep(.1)
            log.debug("Lost Vector object, terminating video stream")
            p.stdin.close()
            p.wait()
        except Exception as e:
            log.debug("Vector Video Exception! {}".format(e))
            p.stdin.close()
            p.wait()
            pass               
    
