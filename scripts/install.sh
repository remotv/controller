#!/bin/bash
# Remo installer script
# See LICENSE for copyright and license details
# When editing this file, it is advisable to enable word wrap, and set your line
# endings from CRLF to LF. (THIS IS VERY IMPORTANT FOR BASH)
# Version 3.0.0

do_robot_owner() {
    ROBOT_OWNER=$(whiptail --inputbox "Please enter your username" 20 60 "" 20 60 1 3>&1 1>&2 2>&3)
    if [ $? -eq 0 ]; then
        sed -i "/^\[robot]/,/^\[/{s/^owner[[:space:]]*=.*/owner=$ROBOT_OWNER/}" $CONF_FILE
    fi
}

do_robot_type() {
    ROBOT_TYPE=$(whiptail --radiolist "Choose a robot type" 20 60 13 \
        "serial_board" "Serial" OFF \
        "motor_hat" "Adafruit Motor Hat" OFF \
        "gopigo2" "GoPiGo2" OFF \
        "gopigo3" "GoPiGo3" OFF \
        "l298n" "L298N" OFF \
        "motozero" "Motozero" OFF \
        "pololu" "Pololu" OFF \
        "adafruit_pwm" "Adafruit PWM" OFF \
        "owi_arm" "OWI Arm" OFF \
        "thunderborg" "ThunderBorg" OFF \
        "none" "None" ON \
        3>&1 1>&2 2>&3)
    RET=$?
    if [ $RET -eq 1 ]; then
        return 0
    elif [ $RET -eq 0 ]; then
        sed -i "/^\[robot]/,/^\[/{s/^type[[:space:]]*=.*/type=$ROBOT_TYPE/}" $CONF_FILE
    fi
}

do_robot_key() {
    ROBOT_KEY=$(whiptail --inputbox "Please enter your robots' API key." 20 60 "" 20 60 1 3>&1 1>&2 2>&3)
    RET=$?
    if [ $RET -eq 1 ]; then
        return 0
    elif [ $RET -eq 0 ]; then
        sed -i "/^\[robot]/,/^\[/{s/^robot_key[[:space:]]*=.*/robot_key=$ROBOT_KEY/}" $CONF_FILE
    fi
}

REPO_DIR="/home/$USER/remotv"
CONF_FILE="$REPO_DIR/controller.conf"
whiptail --yesno "You are about to install everything needed to get your robot connected to remo.tv. This script assumes you have done the necessary steps to add a robot to the site.

Ready to start?" 20 60 1
if [ $? -eq 1 ]; then   # user pressed no
    
    exit 0
fi

sudo apt-get update
sudo apt-get upgrade --assume-yes
sudo apt-get install ffmpeg python3-serial python3-dev libgnutls28-dev espeak python3-smbus python3-pip git --assume-yes

git clone https://github.com/remotv/controller.git $REPO_DIR
python3 -m venv $REPO_DIR/.venv
source $REPO_DIR/.venv/bin/activate
python3 -m pip install -r $REPO_DIR/requirements.txt
cp $REPO_DIR/controller.sample.conf $CONF_FILE

do_robot_owner
do_robot_key
do_robot_type

cp $REPO_DIR/scripts/start_robot /home/$USER/start_robot
chmod +x /home/$USER/start_robot

(crontab -l 2>/dev/null; echo "@reboot /home/$USER/start_robot") | crontab -

whiptail --msgbox "Installation is now complete. Please reboot your robot. See you on remo.tv!"  20 60 1
