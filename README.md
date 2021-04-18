## remo.tv is an open telerobotics platform designed for controling and sharing control of robots online in real time.
## WARNING: This software is currently under development, so you may encounter frequent issues as updates are made. You can check out the [wiki](https://docs.remo.tv) for a more indepth view of what's currently supported.
This controller software is designed to run on your robot and will connect with our development server. It's tuned to support Raspberry Pi based robots, however there is extensive support for other hardware configurations.

## Basic setup
If this is your first time working with a Raspberry Pi or Linux, we recommend following our [initialization tutorial](https://docs.remo.tv/en/stable/controller/getting_started.html) to get started.

## Installing remotv control scripts on a Raspberry Pi

If doing things manually isn't your style, we made an [optional guided installation](https://docs.remo.tv/en/stable/controller/guided_installation.html) script that handles mostly everything for you.

The RasPi will need the following things install so it can talk to your motors and talk to the internet. Make sure you don’t get any errors in the console when doing the step below. If you have an issue, you can run this line again, and that will usually fix it!

1. Install the required software libraries and tools. Make sure you don’t get any errors in the console when doing the step below. If you have an issue, you can run this line again, and that will usually fix it!

   ```sh
   sudo apt update
   sudo apt upgrade -y
   sudo apt install ffmpeg python-serial python-dev libgnutls28-dev espeak python-smbus python-pip git
   ```

2. Download the remotv control scripts from our github

   ```sh
   git clone https://github.com/remotv/controller.git ~/remotv
   ```

3. Install python requirements

   ```sh
   sudo python -m pip install -r ~/remotv/requirements.txt
   ```

4. Open the new `remotv` directory

   ```sh
   cd remotv
   ```

5. Copy `controller.sample.conf` to `controller.conf`

   ```sh
   cp controller.sample.conf controller.conf
   ```

## Configure the controller

1. Edit the `controller.conf` file created in the previous section.
   ```sh
   nano controller.conf
   ```
2. Configure the `[robot]` section

   - `owner` should be the username you have registered the robot under on the remo.tv site.
   - `robot_key` is the API key for your robot that you made on the site.
      - Your API key is LONG. It should look something like `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6InJib3QtNTVjZjJmMjUtNjBhNS00ZDJkLTk5YzMtOGZmOGRiYWU4ZDQ1IiwiaWF0IjoxNTczNTExMDA2LCJzdWIiOiIifQ.LGXSBSyQ4T4X5xU_w3QJD6R3lLjrrkw_QktOIDzRW5U`. If it is not this long, you have not copied the full key.
   - `turn_delay` is only used by the `motor_hat` and `mdd10`. This changes how long your bot turns for. I suggest you leave this at the default value until after you bot is moving.
   - `straight_delay` is only used by the `motor_hat` and `mdd10`. This changes how long your bot turns for. I suggest you leave this at the default value until after you bot is moving.
   - `type` should be the hardware type for the motor controller of your bot. Available types are currently.
     - `adafruit_pwm`
     - `cozmo`
     - `gopigo2`
     - `gopigo3`
     - `l298n`
     - `maestro-serv`
     - `max7219`
     - `mc33926`
     - `mdd10`
     - `motor_hat`
     - `motozero`
     - `none`
     - `owi_arm`
     - `pololu`
     - `serial_board`
     - `telly`
     - `thunderborg`
     - `megapi_board`
   - Configure your hardwares section. Each hardware type can have their own section it the controller. Look through the file for a section named the same as your hardware controller. If the section exists, read through it and adjust the variable as required.

3. Configure the `[camera]` section
   - `no-mic` This allows the microphone to be disabled.
   - `no-camera` This allows the camera to be disabled.
   - `type` This sets the audio / video handler to use. Currently only ffmpeg and ffmpeg-arecord are supported.
   - `x_res` Sets the resolution for the x axis.
   - `y_res` Sets the resolution for the y axis.
   - `camera_device` Sets the device name for the camera.
   - `audio_hw_num` Set the audio hardware number for the microphone.
4. Configure the `[tts]` section
   - `tts_volume` This is the volume level you want your bot to start with.
   - `anon_tts` This allows you to enable or disable anonymous users access to your bots TTS features.
   - `filter_url_tts` This option allows URLs pasted into chat to be blocked from the TTS function.
   - `ext_chat` This enables or disables the extended chat functions.
   - `hw_hum` This is the ALSA hardware number for your pi. 0 is the first sound card and should work for most bots.
   - `type` should be the type of TTS software you are using. The currently supported TTS types are. espeak was installed in the previous steps, and makes a good default tts.
     - `espeak`
     - `fesitval`
     - `pico`
     - Amazon Polly (`polly`)
     - `cozmo_tts`
     - `google_cloud`

## Setting up the remotv service on the Raspberry Pi

1. Link the service file to systemctl

   ```sh
   sudo systemctl link /home/pi/remotv/script/remotv.service
   ```

2. Enable the service to run at startup

   ```sh
   sudo systemctl enable remotv.service
   ```

3. Start the service

   ```sh
   sudo systemctl start remotv.service
   ```

# Hardware Compatibility

The following hardware is supported.

- Adafruit Motor Hat
- Adafruit PWM / Servo Hat
- Anki Cozmo
- Cytron MDD10 10 Amp Motor Driver
- GoPiGo 2
- GoPiGo 3
- L298N Dual Motor Controller
- Pololu Maestro Servo Controller (experimental)
- MAX7219 SPI Led Driver
- MotoZero 4 Motor Controller
- MQTT Publish commands to a local MQTT Broker
- OWI 535 Robotic Arm (USB controller)
- Serial Based controllers (Parallaxy or Arduinos)
- PiBorg ThunderBorg Motor Driver
- Pololu Dual MC33926 Motor Driver (experimental)
- Pololu DRV8835 Dual Motor Driver
- MegaPi by Makeblock

Missing something? You can add it, open source! Instructions for adding new hardware can be found [here.](https://docs.remo.tv/en/stable/controller/hardware/extending.html)

## Chat Commands

When `ext_chat` is enabled, the following chat commands are available. To use, just type them into the chat box on your bots page. These chat commands have no effect on how the site behaves, they only affect the bot. There are some functions that duplicate functions on the site. These changes are not saved and are lost on reboot.

- `.devmode X` Set dev mode. In dev mode, only the owner can drive. If demode is set to mods, your local mods can also drive [on|off|mods].
- `.anon control X` Sets if anonymous users can drive your bot [on|off].
- `.anon tts X` Sets if anonymous users messages are passed to TTS [on|of].
- `.anon X` Sets both anonymous control and tts access [on|off].
- `.tts X` Mute the bots TTS [mute|unmute]
- `.ban NAME` Ban user NAME from controlling your bots
- `.unban NAME` remove user NAME from the ban list
- `.timeout NAME` Timeout user NAME from controlling your bots for 5 minutes
- `.untimeout NAME` remove user NAME from the timeout list.
- `.brightness X` set the camera brightness [0..255]
- `.contrast X` set the camera contrast [0..255]
- `.saturation X` set the camera saturation [0..255]
- `.stationary` Toggles stationary mode on and off. When enabled, forward / backward commands will be blocked.

Hardware modules can have their own hardware specific TTS commands.

# Instructions for Specific Hardware Configurations

## Cozmo

For Anki Cozmo on Mac or Linux, please see the intructions [here](https://docs.remo.tv/en/stable/controller/hardware/cozmo.html).
For Windows instructions, please see the instructions [here](https://docs.remo.tv/en/stable/controller/hardware/cozmo-win.html).

## GoPiGo3

For GoPiGo3, you will need to install the gopigo3 python module (which is different than older versions). It will need to be installed with the installation script from Dexter. Also, `PYTHONPATH` needs to be set to `/home/pi/Dexter/GoPiGo3/Software/Python`

Refer to this:
https://github.com/DexterInd/GoPiGo3

```sh
sudo git clone http://www.github.com/DexterInd/GoPiGo3.git /home/pi/Dexter/GoPiGo3
sudo bash /home/pi/Dexter/GoPiGo3/Install/install.sh
sudo reboot
```

## Adafruit Motor Hat

Install [motor HAT software](https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/installing-software):

## Adafruit PWM / Servo Hat

Install [PWM / Servo hat software](https://learn.adafruit.com/adafruit-16-channel-pwm-servo-hat-for-raspberry-pi/using-the-python-library)

## Pololu Maestro Servo Controller

Install [Maestro Servon controller library](https://github.com/FRC4564/Maestro) into the hardware/ subdirectory.

## Pololu DRV8835 Motor Driver

Install [DRV8835 Motor Driver library](https://github.com/pololu/drv8835-motor-driver-rpi)

## Pololu MC33926 Motor Driver

Install [MC33926 Motor Driver library](https://github.com/pololu/dual-mc33926-motor-driver-rpi)

# Check out the [Wiki](https://docs.remo.tv) for more information

# A note about the Raspi Cam Module

Sometimes enabling the Raspberry Pi Camera module in `raspi-config` doesn't completely load the kernel drivers for it. If you don't see `/dev/video0` on your system, or `controller.py` complains about not finding it, then do the following:

1. Enable the kernel module for your current session:

```sh
sudo modprobe bcm2835-v4l2
```

2. Tell the operating system to load the kernel module at boot going forward:

```sh
sudo cat 'bcm2835-v4l2' >> /etc/modules
```

Now you should see `video0` if you do `ls /dev/ | grep video`
