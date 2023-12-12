from video.ffmpeg_process import *
import video.ffmpeg as ffmpeg
import networking
import logging
import time

log = logging.getLogger('RemoTV.video.ffmpeg-libcamera')

# This is a pretty ugly way to overload the startAudioCapture(), but it's also
# the only way that seems to work. Otherwise, when called internally to the
# ffmpeg module, the original function gets called.
def setup(robot_config):
    ffmpeg.setup(robot_config)
    ffmpeg.startVideoCapture=startVideoCapture


def startVideoCapture():
    global video_process

    while not networking.authenticated:
        time.sleep(1)

    if networking.internetStatus:
       videoCommandLine = ('libcamera-vid -t 0 --width {xres} --height {yres}'
                           ' --codec yuv420 -o - | ')
       videoCommandLine += '{ffmpeg} -f rawvideo -framerate {framerate}'
       videoCommandLine += ' -video_size {xres}x{yres}'

       videoCommandLine += (' -r {framerate} {in_options} -i - {video_filter}'
                        ' -f mpegts -codec:v {video_codec} -b:v {video_bitrate}k -bf 0'
                        ' -muxdelay 0.001 {out_options}'
                        ' -headers "Authorization: Bearer {robotKey}"'
                        ' http://{server}/transmit?name={channel}-video')

       videoCommandLine = videoCommandLine.format(ffmpeg=ffmpeg.ffmpeg_location,
                            input_format=ffmpeg.video_input_format,
                            framerate=ffmpeg.video_framerate,
                            in_options=ffmpeg.video_input_options,
                            video_device=ffmpeg.video_device,
                            video_filter=ffmpeg.video_filter,
                            video_codec=ffmpeg.video_codec,
                            video_bitrate=ffmpeg.video_bitrate,
                            out_options=ffmpeg.video_output_options,
                            server=ffmpeg.server,
                            channel=networking.channel_id,
                            xres=ffmpeg.x_res,
                            yres=ffmpeg.y_res,
                            robotKey=ffmpeg.robotKey)

       log.debug("videoCommandLine : %s", videoCommandLine)
       ffmpeg.startFFMPEG(videoCommandLine, 'Video',  ffmpeg.atExitVideoCapture, 'video_process')

    else:
       log.debug("No Internet/Server : sleeping video start for 15 seconds")
       time.sleep(15)

def start():
   ffmpeg.start()
