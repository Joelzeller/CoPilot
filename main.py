import kivy
#kivy.require('1.0.6')
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from math import cos, sin, pi
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.label import Label
from kivy.logger import Logger
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, SlideTransition
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.scatter import Scatter
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import AsyncImage
from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.image import Image
from kivymd.button import MDIconButton
from kivymd.label import MDLabel
from kivymd.list import ILeftBody, ILeftBodyTouch, IRightBodyTouch
from kivymd.theming import ThemeManager
from kivymd.dialog import MDDialog
import kivymd.snackbar as Snackbar
import re


#from kivy.garden.mapview import MapView

#I know global variables are the devil....but they are so easy

#set to 1 to disable all GPIO, temp probe, and obd stuff
global developermode
developermode = 1
global devtaps #used to keep track of taps on settings label - 5 will force devmode
devtaps = 0

global version
version = "V2.2.0"
#2/14/2017
#Created by Joel Zeller

# For PC dev work -----------------------
if developermode == 1:
    from kivy.config import Config
    Config.set('graphics', 'width', '800')
    Config.set('graphics', 'height', '480')

    from kivy.core.window import Window
    Window.size = (800, 480)
# ---------------------------------------

if developermode == 0:
    import RPi.GPIO as GPIO
    import obd
    import serial
global adxl345
import sys
import datetime
import time
import os
import subprocess
import glob
import math
import socket
import pickle

#disabled for now - doesn't play nice when not connected to a network
cmd = "ip addr show wlan0 | grep inet | awk '{print $2}' | cut -d/ -f1"
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
global ip
#ip = get_ip_address()

#_____________________________________________________________
#GPIO SETUP

#name GPIO pins
seekupPin = 13
seekdownPin = 19
auxPin = 16
amfmPin = 26
garagePin = 20
radarPin = 21
ledsPin = 5
driverwindowdownPin = 17  
driverwindowupPin = 15 
passwindowdownPin = 27 
passwindowupPin = 18 

HotKey1Pin = 12
HotKey2Pin = 6

if developermode == 0:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(seekupPin, GPIO.OUT)
    GPIO.setup(seekdownPin, GPIO.OUT)
    GPIO.setup(auxPin, GPIO.OUT)
    GPIO.setup(amfmPin, GPIO.OUT)
    GPIO.setup(garagePin, GPIO.OUT)
    GPIO.setup(radarPin, GPIO.OUT)
    GPIO.setup(ledsPin, GPIO.OUT)
    GPIO.setup(driverwindowdownPin, GPIO.OUT)
    GPIO.setup(driverwindowupPin, GPIO.OUT)
    GPIO.setup(passwindowdownPin, GPIO.OUT)
    GPIO.setup(passwindowupPin, GPIO.OUT)

    GPIO.setup(HotKey1Pin, GPIO.IN)
    GPIO.setup(HotKey2Pin, GPIO.IN)

#initial state of GPIO

    GPIO.output(seekupPin, GPIO.HIGH)
    GPIO.output(seekdownPin, GPIO.HIGH)
    GPIO.output(auxPin, GPIO.HIGH)
    GPIO.output(amfmPin, GPIO.HIGH)
    GPIO.output(garagePin, GPIO.HIGH)
    GPIO.output(radarPin, GPIO.HIGH)
    GPIO.output(ledsPin, GPIO.LOW)
    GPIO.output(driverwindowdownPin, GPIO.HIGH)
    GPIO.output(driverwindowupPin, GPIO.HIGH)
    GPIO.output(passwindowdownPin, GPIO.HIGH)
    GPIO.output(passwindowupPin, GPIO.HIGH)

#_________________________________________________________________
#OBD STUFF
global OBDON #var for displaying obd gauges
OBDVAR = 0
#0 - OFF
#1 - Digital Speed
#2 - Digital Tach
#3 - Graphic
#4 - Coolant Temp
#5 - Intake Temp
#6 - Engine Load

#_________________________________________________________________
#TEMP PROBE STUFF
global TempProbePresent #set to 1 if temp probe is connected, 0 if not
TempProbePresent = 1

global AccelPresent #set to 1 if adxl345 accelerometer is present
AccelPresent = 0

if developermode == 1:
    TempProbePresent = 0
    AccelPresent = 0

if AccelPresent == 1:
    from adxl345 import ADXL345
    adxl345 = ADXL345()

if TempProbePresent == 1:
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
    base_dir = '/sys/bus/w1/devices/'
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'

global temp_f #make this var global for use in messages
temp_f = 0

global TEMPON #var for displaying cabin temp widget
TEMPON = 0

global ACCELON
ACCELON = 0

global bluetoothdevicemac
bluetoothdevicemac = 'F0_D1_A9_C9_86_3E' #Enter your smartphones mac address here so its audio can be controlled from the audio app
global BLUETOOTHON
BLUETOOTHON = 0
global bluetoothdata
bluetoothdata = ['Title','','Album','','Artist',''] #Default - only shown when bluetooth enabled


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp():
    global temp_f
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        #time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c_raw = float(temp_string) / 1000.0
        temp_f_raw = temp_c_raw * 9.0 / 5.0 + 32.0
        temp_f = "{0:.0f}".format(temp_f_raw) #only whole numbers

#_________________________________________________________________
#VARIABLES

#varibles from text file:
global theme
global wallpaper
global hotkey1string
global hotkey2string
global oildatemonth
global oildateday
global oildateyear
global oilmileage
global oilnotify
global speedlimit
global rpmredline

f = open('savedata.txt', 'r+') # read from text file
theme = f.readline()
theme = theme.rstrip() #to remove \n from string
wallpaper = int(f.readline())
hotkey1string = f.readline()
hotkey1string = hotkey1string.rstrip()
hotkey2string = f.readline()
hotkey2string = hotkey2string.rstrip()
oildatemonth = int(f.readline())
oildateday = int(f.readline())
oildateyear = int(f.readline())
oilmileage = int(f.readline())
oilnotify = int(f.readline())
speedlimit = int(f.readline())
rpmredline = int(f.readline())
f.close()

global SEEKUPON 
SEEKUPON = 0

global SEEKDOWNON 
SEEKDOWNON = 0

global AUXON 
AUXON = 0

global AMFMON 
AMFMON = 0

global GARAGEON 
GARAGEON = 0

global RADARON 
RADARON = 0

global LEDSON 
LEDSON = 0

global WINDOWSDOWNON 
WINDOWSDOWNON = 0

global WINDOWSUPON 
WINDOWSUPON = 0

# window debug vars
global DRIVERUPON
DRIVERUPON = 0
global DRIVERDOWNON
DRIVERDOWNON = 0
global PASSENGERUPON
PASSENGERUPON = 0
global PASSENGERDOWNON
PASSENGERDOWNON = 0

global clock
clock = 0

global analog
analog = 1

global message
message = 0

global swminute
swminute = 0

global swsecond
swsecond = 0

global swtenth
swtenth = 0

global swactive
swactive = 0

global swstring
swstring = 0

global testvar
testvar = 0

global testvar2
testvar2 = 0

global screenon
screenon = 1

global windowuptime #time it takes front windows to rise (secs)
windowuptime = 7

global windowdowntime #time it takes front windows to open (secs)
windowdowntime = 6

global clocktheme
clocktheme = 2

global launch_start_time
launch_start_time = 0

global animation_start_time
animation_start_time = 0

global time_second_mod
time_second_mod = 0

#OBD Global vars
global OBDconnection
OBDconnection = 0 #connection is off by default - will be turned on in obd page

global cmd_RPM
global cmd_SPEED
global cmd_CoolantTemp
global cmd_IntakeTemp
global cmd_Load

global maxRPM
maxRPM = 0

global devobd
devobd = 0
global incobd #amount to step in dev mode - obd pages
incobd = 1

global changeoil
changeoil = 0
if oilnotify == 1:
    if int(time.strftime("%Y")) > oildateyear:
        changeoil = 1
    if int(time.strftime("%m")) >= oildatemonth:
        if int(time.strftime("%Y")) > oildateyear:
            changeoil = 1
    if int(time.strftime("%d")) >= oildateday:
        if int(time.strftime("%m")) >= oildatemonth:
            if int(time.strftime("%Y")) >= oildateyear:
                changeoil = 1
#__________________________________________________________________
#HOTKEY STUFF

def HotKey1(channel):
    global hotkey1string
    global screenon
    global windowuptime
    global windowdowntime
    global WINDOWSUPON
    global WINDOWSDOWNON
    if hotkey1string == "Seek Up":
        Clock.schedule_once(seekup_callback)
        Clock.schedule_once(seekup_callback,.1)

    if hotkey1string == "Seek Down":
        Clock.schedule_once(seekdown_callback)
        Clock.schedule_once(seekdown_callback,.1)
    if hotkey1string == "Garage":
        Clock.schedule_once(garage_callback)
        Clock.schedule_once(garage_callback,.1)
    if hotkey1string == "Radar":
        Clock.schedule_once(radar_callback)
    if hotkey1string == "Cup Lights":
        Clock.schedule_once(leds_callback)

    if hotkey1string == "Windows Up":
        if WINDOWSDOWNON == 0: #only works when windows down isnt running
            Clock.schedule_once(windowsup_callback)
            Clock.schedule_once(windowsupOFF_callback, windowuptime)
            return
        if WINDOWSUPON == 1:
            Clock.schedule_once(windowsupOFF_callback) #if windows going up while pushed, will cancel and stop windows

    if hotkey1string == "Windows Down":
        if WINDOWSUPON == 0: #only works when windows up isnt running
            Clock.schedule_once(windowsdown_callback)
            Clock.schedule_once(windowsdownOFF_callback, windowdowntime)
            return
        if WINDOWSDOWNON == 1:
            Clock.schedule_once(windowsdownOFF_callback) #if windows going down while pushed, will cancel and stop windows

    if hotkey1string == "Screen Toggle":
        if screenon == 1:
            os.system("sudo echo 1 > /sys/class/backlight/rpi_backlight/bl_power") #turns screen off
            screenon = 0
            return
        if screenon == 0:
            os.system("sudo echo 0 > /sys/class/backlight/rpi_backlight/bl_power") #turns screen on
            screenon = 1
            return
    if hotkey1string == "None":
        return
    

def HotKey2(channel):
    global hotkey2string
    global screenon
    global windowuptime
    global windowdowntime
    global WINDOWSUPON
    global WINDOWSDOWNON
    if hotkey2string == "Seek Up":
        Clock.schedule_once(seekup_callback)
        Clock.schedule_once(seekup_callback,.1)
    if hotkey2string == "Seek Down":
        Clock.schedule_once(seekdown_callback)
        Clock.schedule_once(seekdown_callback,.1)
    if hotkey2string == "Garage":
        Clock.schedule_once(garage_callback)
        Clock.schedule_once(garage_callback,.1)
    if hotkey2string == "Radar":
        Clock.schedule_once(radar_callback)
    if hotkey2string == "Cup Lights":
        Clock.schedule_once(leds_callback)
        
    if hotkey2string == "Windows Up":
        if WINDOWSDOWNON == 0: #only works when windows down isnt running
            Clock.schedule_once(windowsup_callback)
            Clock.schedule_once(windowsupOFF_callback, windowuptime)
            return
        if WINDOWSUPON == 1:
            Clock.schedule_once(windowsupOFF_callback) #if windows going up while pushed, will cancel and stop windows

    if hotkey2string == "Windows Down":
        if WINDOWSUPON == 0: #only works when windows up isnt running
            Clock.schedule_once(windowsdown_callback)
            Clock.schedule_once(windowsdownOFF_callback, windowdowntime)
            return
        if WINDOWSDOWNON == 1:
            Clock.schedule_once(windowsdownOFF_callback) #if windows going down while pushed, will cancel and stop windows

    if hotkey2string == "Screen Toggle":
        if screenon == 1:
            os.system("sudo echo 1 > /sys/class/backlight/rpi_backlight/bl_power") #turns screen off
            screenon = 0
            return
        if screenon == 0:
            os.system("sudo echo 0 > /sys/class/backlight/rpi_backlight/bl_power") #turns screen on
            screenon = 1
            return
    if hotkey2string == "None":
        return

if developermode == 0:
    GPIO.add_event_detect(HotKey1Pin, GPIO.FALLING, callback=HotKey1, bouncetime=3000)
    GPIO.add_event_detect(HotKey2Pin, GPIO.FALLING, callback=HotKey2, bouncetime=3000)

#__________________________________________________________________
#DEFINE CLASSES

#ROOT CLASSES

class ROOT(FloatLayout):
    pass
class QUICKEYSLayout(FloatLayout):
    pass

        #MAIN SCREEN CLASSES

class MainScreen(Screen):
    pass
class AudioScreen(Screen):
    pass
class PerfScreen(Screen):
    pass
class AppsScreen(Screen):
    pass
class ControlsScreen(Screen):
    pass
class SettingsScreen(Screen):
    pass
class KillScreen(Screen):
    pass

        #APP SCREEN CLASSES

class PaintScreen(Screen):
    pass
class FilesScreen(Screen):
    pass
class LogoScreen(Screen):
    pass
class ClockChooserScreen(Screen):
    pass
class ClassicClockScreen(Screen):
    pass
class SportClockScreen(Screen):
    pass
class ExecutiveClockScreen(Screen):
    pass
class DayGaugeClockScreen(Screen):
    pass
class NightGaugeClockScreen(Screen):
    pass
class WormsClockScreen(Screen):
    pass
class InfoClockScreen(Screen):
    pass
class PhotoClockScreen(Screen):
    pass
class TestAppScreen(Screen):
    pass
class MaintenanceScreen(Screen):
    pass
class MaintenanceSetOilInfoScreen(Screen):
    pass
class GPSScreen(Screen):
    pass
class StopwatchScreen(Screen):
    pass
class DiagnosticsScreen(Screen):
    pass
class SystemDebugScreen(Screen):
    pass
class WindowDebugScreen(Screen):
    pass
class LaunchControlSetupScreen(Screen):
    pass
class LaunchControlScreen(Screen):
    pass
class PhotosScreen(Screen):
    pass
class GaugeSelectScreen(Screen):
    pass
class OBDTachsScreen(Screen):
    pass
class OBDSpeedosScreen(Screen):
    pass
class OBDDiagnosticsScreen(Screen):
    pass
class GaugeSelectScreen(Screen):
    pass
class GaugeSelectScreen(Screen):
    pass
class OBDDigitalSpeedoScreen(Screen):
    pass
class OBDDigitalTachScreen(Screen):
    pass
class OBDGraphicTachScreen(Screen):
    pass
class OBDGraphicTach2Screen(Screen):
    pass
class OBDCoolantScreen(Screen):
    pass
class OBDIntakeTempScreen(Screen):
    pass
class OBDLoadScreen(Screen):
    pass
class OBDSettingsScreen(Screen):
    pass
class AccelerometerScreen(Screen):
    pass
class NOSScreen(Screen):
    pass
class WallpaperSelectScreen(Screen):
    pass
class HotKey1ChooserScreen(Screen):
    pass
class HotKey2ChooserScreen(Screen):
    pass
class OffScreen(Screen):
    pass

#APP CLASSES
class Painter(Widget): #Paint App
    
    def on_touch_down(self, touch):
        with self.canvas:
            touch.ud["line"] = Line(points=(touch.x, touch.y))

    def on_touch_move(self, touch):
        touch.ud["line"].points += [touch.x, touch.y]

#KIVYMD classes
class IconLeftSampleWidget(ILeftBodyTouch, MDIconButton):
    pass


#_________________________________________________________________
#MAINAPP

class MainApp(App):
    theme_cls = ThemeManager()
    version = StringProperty()
    timenow = StringProperty()
    timenow_hour = NumericProperty(0)
    timenow_minute = NumericProperty(0)
    timenow_second = NumericProperty(0)
    launch_start_time = NumericProperty(0)
    time_second_mod = NumericProperty(0)
    datenow = StringProperty()
    daynow = StringProperty()
    yearnow = StringProperty()
    ampm = StringProperty()
    tempnow = StringProperty()
    CPUtempnow = StringProperty()
    corevoltagenow = StringProperty()
    stopwatchnow = StringProperty()
    stopwatchsecnow = ObjectProperty()
    stopwatchmilnow = ObjectProperty()
    HKonenow = StringProperty()
    HKtwonow = StringProperty()
    radariconsource = StringProperty()
    lightsiconsource = StringProperty()
    wallpapernow = StringProperty()
    obdspeed = StringProperty()
    obdspeedval = ObjectProperty()
    obdspeedlimitval = ObjectProperty(speedlimit)
    obdspeedmax = StringProperty()
    obdRPM = StringProperty()
    obdRPMval = NumericProperty(0)
    obdRPMmax = StringProperty()
    maxRPMvar = ObjectProperty()
    obdRPMredline = ObjectProperty(rpmredline)
    obdcoolanttemp = StringProperty()
    obdintaketemp = StringProperty()
    obdengineload = StringProperty()
    obdengineloadval = ObjectProperty()
    oildatemonth = ObjectProperty()
    oildateday = ObjectProperty()
    oildateyear = ObjectProperty()
    oilmileage = ObjectProperty()
    oilnotify = ObjectProperty()
    changeoil = ObjectProperty()
    ip = StringProperty()
    accelx = NumericProperty(0)
    accely = NumericProperty(0)
    bluetoothtitle = StringProperty()
    bluetoothartist = StringProperty()
    bluetoothduration = NumericProperty(0)
    bluetoothprogress = NumericProperty(0)

    theme_cls.theme_style = "Dark"
    #theme_cls.primary_palette = "Indigo"
    global theme
    theme_cls.primary_palette = theme

    def updatetime(self, *args):
        time = datetime.datetime.now()
        time_hour = time.strftime("%I")  # time_hour
        if time_hour[0] == "0":  # one digit format
            time_hour = " " + time_hour[1]
        time_minute = time.strftime("%M")  # time_minute
        timenow = time_hour + ":" + time_minute  # create sting format (hour:minute)
        self.timenow = timenow
        #self.timenow = "3:14" # for screenshots
        self.timenow_hour = time.hour
        self.timenow_minute = time.minute
        self.timenow_second = time.second


        global time_second_mod
        time_second_mod = int(float(time_second_mod)) + 1
        if time_second_mod > 10000000:  # doesnt allow this var to get too big
            time_second_mod = 0
        self.time_second_mod = time_second_mod
        global launch_start_time
        self.launch_start_time = launch_start_time

    def updatedate(self, *args):
        day = time.strftime("%A") #current day of week
        month = time.strftime("%B") #current month
        date = time.strftime("%d")  #current day of month
        year = time.strftime("%Y")  #current year
        ampm = time.strftime("%p")  #AM or PM
        if date[0] == "0":  # one digit format for day of month
            date = " " + date[1]
        datenow = month + " " + date
        self.datenow = datenow
        self.daynow = day
        self.yearnow = year
        self.ampm = ampm

    def updatetemp(self, *args):
        temp_f_string = str(temp_f)
        #if int(float(animation_start_time))+5 <= int(float(time_second_mod)): #animation is delayed for better asthetics
        global TEMPON
        if TEMPON == 1:
            if TempProbePresent == 1:
                    read_temp()
                    tempnow = " " + temp_f_string + u'\N{DEGREE SIGN}'
            if TempProbePresent == 0:
                    tempnow = " " + "72" + u'\N{DEGREE SIGN}'
        if TEMPON == 0:
            if TempProbePresent == 1:
                    tempnow = " " + temp_f_string + u'\N{DEGREE SIGN}'
            if TempProbePresent == 0:
                    tempnow = " " + "72" + u'\N{DEGREE SIGN}'

        self.tempnow = tempnow

    def updatevariables(self, *args):
        global swminute
        global swsecond
        global swtenth
        global swactive
        global swstring
        global swminutestring
        global swsecondstring
        global version
        global devtaps
        if swactive == 1:
            swtenth += 1
            if swtenth == 10:
                swtenth = 0
                swsecond += 1
            if swsecond == 60:
                swsecond = 0
                swminute += 1

        # fortmatting for stopwatch display - outside of if statement because watch will run in background
        if swsecond < 10:
            swsecondstring = "0" + str(swsecond)
        else:
            swsecondstring = str(swsecond)
        if swminute < 10:
            swminutestring = "0" + str(swminute)
        else:
            swminutestring = str(swminute)
        swstring = (swminutestring + ":" + swsecondstring + ":" + str(swtenth) + "0")
        #set vars
        self.stopwatchnow = swstring
        self.stopwatchsecnow = swsecond + (swtenth*.1)
        self.HKonenow = hotkey1string
        self.HKtwonow = hotkey2string
        self.version = version
        #self.ip = ip
        self.ip = "WIP"
        self.devtaps = devtaps
        self.oildatemonth = oildatemonth
        self.oildateday = oildateday
        self.oildateyear = oildateyear
        self.oilmileage = oilmileage
        self.oilnotify = oilnotify
        self.changeoil = changeoil

        global BLUETOOTHON
        if BLUETOOTHON == 1:
            if int(float(animation_start_time)) + 5 <= int(float(time_second_mod)):
                try:
                    if DISPLAYBTDATA == 1:
                        bluetoothdataraw = os.popen('dbus-send --system --type=method_call --print-reply --dest=org.bluez /org/bluez/hci0/dev_' + bluetoothdevicemac + '/player0 org.freedesktop.DBus.Properties.Get string:org.bluez.MediaPlayer1 string:Track').read()
                        bluetoothduration = int((bluetoothdataraw.split("uint32"))[1].split('\n')[0])

                        bluetoothprogressraw = os.popen('dbus-send --system --type=method_call --print-reply --dest=org.bluez /org/bluez/hci0/dev_' + bluetoothdevicemac + '/player0 org.freedesktop.DBus.Properties.Get string:org.bluez.MediaPlayer1 string:Position').read()
                        bluetoothprogress = int((bluetoothprogressraw.split("uint32"))[1].split('\n')[0])

                        bluetoothdata = bluetoothdataraw.split('"')[1::2]  # takes string and finds things in quotes - 1=title, 3=album, 5=artist
                        self.bluetoothtitle = bluetoothdata[1]
                        self.bluetoothartist = bluetoothdata[5]
                        #percent = bluetoothprogress/bluetoothduration
                        #print str(bluetoothprogress)
                        #print str(bluetoothduration)
                        self.bluetoothduration = bluetoothduration
                        self.bluetoothprogress = bluetoothprogress
                    else:
                        self.bluetoothtitle = ''
                        self.bluetoothartist = ''
                        self.bluetoothduration = 0
                        self.bluetoothprogress = 0
                except:
                    BLUETOOTHON = 0
        if BLUETOOTHON == 0: #show nothing when bluetooth is off
            self.bluetoothtitle = ''
            self.bluetoothartist = ''
            self.bluetoothduration = 0
            self.bluetoothprogress = 0

        global theme
        theme = self.theme_cls.primary_palette
        if RADARON == 1:
            self.radariconsource = 'data/icons/radarindicator.png'
        if RADARON == 0:
            self.radariconsource = 'data/icons/null.png'
        if LEDSON == 1:
            self.lightsiconsource = 'data/icons/app_icons/lights_icon_on.png'
        if LEDSON == 0:
            self.lightsiconsource = 'data/icons/app_icons/lights_icon.png'

        if wallpaper == 0:
            self.wallpapernow = 'data/wallpapers/greenmaterial.png'
        if wallpaper == 1:
            self.wallpapernow = 'data/wallpapers/blackgreenmaterial.png'
        if wallpaper == 2:
            self.wallpapernow = 'data/wallpapers/darkgreymaterial2.png'
        if wallpaper == 3:
            self.wallpapernow = 'data/wallpapers/polymountain.png'
        if wallpaper == 4:
            self.wallpapernow = 'data/wallpapers/trianglematerial.png'
        if wallpaper == 5:
            self.wallpapernow = 'data/wallpapers/blackredmaterial.png'
        if wallpaper == 6:
            self.wallpapernow = 'data/wallpapers/greybluematerial.png'
        if wallpaper == 7:
            self.wallpapernow = 'data/wallpapers/lightblueblackmaterial.png'
        if wallpaper == 8:
            self.wallpapernow = 'data/wallpapers/greyplain.png'
        if wallpaper == 9:
            self.wallpapernow = 'data/wallpapers/stopwatchblue.png'
        if wallpaper == 10:
            self.wallpapernow = 'data/wallpapers/polycube.png'
        if wallpaper == 11:
            self.wallpapernow = 'data/wallpapers/polyvalley.png'
        if wallpaper == 12:
            self.wallpapernow = 'data/wallpapers/purplebluematerial.png'
        if wallpaper == 13:
            self.wallpapernow = 'data/wallpapers/bluegreymaterial.png'
        if wallpaper == 14:
            self.wallpapernow = 'data/wallpapers/redpurplematerial.png'
        if wallpaper == 15:
            self.wallpapernow = 'data/wallpapers/CoPilot_Wallpaper_2.png'
        if wallpaper == 16:
            self.wallpapernow = 'data/wallpapers/blackredmaterial2.png'
        if wallpaper == 17:
            self.wallpapernow = 'data/wallpapers/androidauto.png'
        if wallpaper == 18:
            self.wallpapernow = 'data/wallpapers/tealmaterialdesign.png'
        if wallpaper == 19:
            self.wallpapernow = 'data/wallpapers/blueblackmaterial.png'
        if wallpaper == 20:
            self.wallpapernow = 'data/wallpapers/greenmaterial2.png'
        if wallpaper == 21:
            self.wallpapernow = 'data/wallpapers/redbluematerial.png'
        if wallpaper == 22:
            self.wallpapernow = 'data/wallpapers/blueblackwhitematerial.png'
        if wallpaper == 23:
            self.wallpapernow = 'data/wallpapers/polymountain2.png'
        if wallpaper == 24:
            self.wallpapernow = 'data/wallpapers/blackpoly.png'
        if wallpaper == 25:
            self.wallpapernow = 'data/wallpapers/blackredlacematerial.png'
        if wallpaper == 26:
            self.wallpapernow = 'data/wallpapers/blueredpoly.png'
        if wallpaper == 27:
            self.wallpapernow = 'data/wallpapers/firewaterpoly.png'
        if wallpaper == 28:
            self.wallpapernow = 'data/wallpapers/tanbluepoly.png'

    def updatemessage(self, *args):
        # the logic for what the message says
        if message == 0:
            self.text = " "
        if message == 1:  # used for displaying the CPU temp
            if developermode == 0:
                temperaturestring = subprocess.check_output(["/opt/vc/bin/vcgencmd", "measure_temp"])
                corevoltagestring = subprocess.check_output(["/opt/vc/bin/vcgencmd", "measure_volts core"])
                temperature = (temperaturestring.split('=')[1][:-3])
                corevoltage = (corevoltagestring.split('=')[1][:-3])
                CPUtempnow = temperature + u'\N{DEGREE SIGN}' + "C"
                corevoltagenow = corevoltage + " V"
            if developermode == 1:
                CPUtempnow = "40" + u'\N{DEGREE SIGN}' + "C"
                corevoltagenow = "3.14" + " V"
            self.CPUtempnow = CPUtempnow
            self.corevoltagenow = corevoltagenow

    def updateaccel(self, *args):
        global ACCELON
        if ACCELON == 1:
            if AccelPresent == 1:
                axes = adxl345.getAxes(True)
                self.accelx = axes['x'] - .18 #compensation amount
                self.accely = axes['y'] + .044 #compensation amount
        if ACCELON == 0:
            self.accelx = .5
            self.accely = .1

    def updateOBDdata(self, *args):

        global clocktheme
        global response_RPM_int_adjusted
        global response_SPEED_int_adjusted
        global devobd
        global incobd
        global maxRPM
        global animation_time_start
        global rpmredline
        global speedlimit
        # _____________________________________________________________________________________
        if int(float(animation_start_time)) + 5 <= int(float(time_second_mod)):  # animation is delayed for better asthetics
            if OBDVAR == 0:  # code for no OBD stuff
                self.obdspeed = "0"
                self.obdRPM = "0"
                self.obdcoolanttemp = "0"
                self.obdintaketemp = "0"
                self.obdengineload = "0"

            if OBDVAR == 1:  # code for OBD Digital Speedo
                if developermode == 1:
                    if incobd == 1:
                        devobd = devobd + 1
                    else:
                        devobd = devobd - 1
                    if devobd > 125:
                        incobd = 0
                    if devobd < 1:
                        incobd = 1
                    self.obdspeed = str(devobd)
                    self.obdspeedval = devobd
                    self.obdspeedlimitval = speedlimit
                else:
                    if OBDconnection == 1:
                        response_SPEED = connection.query(cmd_SPEED)  # send the command, and parse the response
                        response_SPEED_string = str(response_SPEED.value)  # change value into a string for comparing to "None"

                        if response_SPEED_string != 'None':  # only proceed if string value is not None

                            response_SPEED_int = int(response_SPEED.value)  # change the var type to int

                            if response_SPEED_int == 0:  # to avoid the formula
                                response_SPEED_int_adjusted = 0
                                self.obdspeed = "0"

                            if response_SPEED_int == 1:  # to avoid the formula
                                response_SPEED_int_adjusted = 1
                                self.obdspeed = "1"

                            if response_SPEED_int == 2:  # to avoid the formula
                                response_SPEED_int_adjusted = 1
                                self.obdspeed = "1"

                            if response_SPEED_int > 2:  # start to apply the formula to speed
                                response_SPEED_int_adjusted = math.floor(((response_SPEED_int) * (.6278)) - .664)  # adjusts number according to formula and rounds down to nearesr whole MPH - sets new adjusted int
                                response_SPEED_string_adjusted = str(response_SPEED_int_adjusted)  # sets string
                                self.obdspeed = response_SPEED_string_adjusted.strip()[:-2]  # set text

                            if  response_SPEED_int_adjusted > 60: #apply new formula after 60 mph - from driving tests
                                response_SPEED_int_adjusted = math.floor((1.0264 * (response_SPEED_int_adjusted)) - 0.6739)
                                response_SPEED_string_adjusted = str(response_SPEED_int_adjusted)  # sets string
                                self.obdspeed = response_SPEED_string_adjusted.strip()[:-2]  # set text


                            self.obdspeedval = response_SPEED_int_adjusted
                            self.obdspeedlimitval = speedlimit

            if OBDVAR == 2:  # code for OBD Digital Tach
                if developermode == 1: #code to simulate 0 to 6750 and back down - for testing purposes
                    if incobd == 1:
                        devobd = devobd + 10
                    else:
                        devobd = devobd - 10
                    if devobd > 6900:
                        incobd = 0
                    if devobd < 100:
                        incobd = 1
                    if devobd > maxRPM:
                        maxRPM = devobd
                    self.obdRPMmax = str(maxRPM)
                    self.obdRPM = str(devobd)
                    self.obdRPMval = devobd
                    self.obdRPMredline = rpmredline
                else:
                    if OBDconnection == 1:
                        response_RPM = connection.query(cmd_RPM)  # send the command, and parse the response

                        response_RPM_string = str(response_RPM.value)  # change value into a string for comparing to "None"

                        if response_RPM_string != 'None':  # only proceed if string value is not None

                            response_RPM_int = int(response_RPM.value)  # set int value
                            response_RPM_int_adjusted = math.floor(response_RPM_int)  # round down to nearest whole RPM
                            if response_RPM_int_adjusted > maxRPM:
                                maxRPM = response_RPM_int_adjusted
                            self.maxRPMvar = maxRPM
                            maxRPM_string = str(maxRPM)
                            maxRPM_string = maxRPM_string.strip()[:-2]  # strip .0 at the end of string
                            response_RPM_string = str(response_RPM_int_adjusted)  # set string value
                            response_RPM_string = response_RPM_string.strip()[:-2]  # strip .0 at the end of string
                            self.obdRPM = response_RPM_string
                            self.obdRPMmax = maxRPM_string
                            self.obdRPMval = response_RPM_int
                            self.obdRPMredline = rpmredline

            if OBDVAR == 4:  # code for OBD Coolant Temp
                if developermode == 1:
                    if incobd == 1:
                        devobd = devobd + 1
                    else:
                        devobd = devobd - 1
                    if devobd > 220:
                        incobd = 0
                    if devobd < 1:
                        incobd = 1
                    self.obdcoolanttemp = str(devobd) + u'\N{DEGREE SIGN}'
                else:
                    if OBDconnection == 1:
                        response_CoolantTemp = connection.query(cmd_CoolantTemp)  # send the command, and parse the response

                        response_CoolantTemp_string = str(response_CoolantTemp.value)  # change value into a string for comparing to "None"

                        if response_CoolantTemp_string != 'None':  # only proceed if string value is not None
                            response_CoolantTemp_int = int(response_CoolantTemp.value) * 9.0 / 5.0 + 32.0  # set int value - change to farenheit
                            response_CoolantTemp_int_adjusted = math.floor(response_CoolantTemp_int)  # round down to nearest whole RPM
                            response_CoolantTemp_string = str(response_CoolantTemp_int_adjusted)  # set string value
                            response_CoolantTemp_string = response_CoolantTemp_string.strip()[:-2]  # strip .0 at the end of string
                            self.obdcoolanttemp = response_CoolantTemp_string + u'\N{DEGREE SIGN}'  # set text

            if OBDVAR == 5:  # code for OBD Intake Temp
                if developermode == 1:
                    if incobd == 1:
                        devobd = devobd + 1
                    else:
                        devobd = devobd - 1
                    if devobd > 120:
                        incobd = 0
                    if devobd < 1:
                        incobd = 1
                    self.obdintaketemp = str(devobd) + u'\N{DEGREE SIGN}'
                else:
                    if OBDconnection == 1:
                        response_IntakeTemp = connection.query(cmd_IntakeTemp)  # send the command, and parse the response

                        response_IntakeTemp_string = str(response_IntakeTemp.value)  # change value into a string for comparing to "None"

                        if response_IntakeTemp_string != 'None':  # only proceed if string value is not None
                            response_IntakeTemp_int = int(response_IntakeTemp.value) * 9.0 / 5.0 + 32.0  # set int value - change to farenheit
                            response_IntakeTemp_int_adjusted = math.floor(response_IntakeTemp_int)  # round down to nearest whole RPM
                            response_IntakeTemp_string = str(response_IntakeTemp_int_adjusted)  # set string value
                            response_IntakeTemp_string = response_IntakeTemp_string.strip()[:-2]  # strip .0 at the end of string
                            self.obdintaketemp = response_IntakeTemp_string + u'\N{DEGREE SIGN}'  # set text

            if OBDVAR == 6:  # code for OBD Engine Load
                if developermode == 1:
                    if incobd == 1:
                        devobd = devobd + 1
                    else:
                        devobd = devobd - 1
                    if devobd > 99:
                        incobd = 0
                    if devobd < 1:
                        incobd = 1
                    self.obdengineload = str(devobd) + '%'
                    self.obdengineloadval = devobd
                else:
                    if OBDconnection == 1:
                        response_Load = connection.query(cmd_Load)  # send the command, and parse the response

                        response_Load_string = str(response_Load.value)  # change value into a string for comparing to "None"

                        if response_Load_string != 'None':  # only proceed if string value is not None
                            response_Load_int = int(response_Load.value)
                            response_Load_int_adjusted = math.floor(response_Load_int)  # round down to nearest whole RPM
                            response_Load_string = str(response_Load_int_adjusted)  # set string value
                            response_Load_string = response_Load_string.strip()[:-2]  # strip .0 at the end of string
                            self.obdengineload = response_Load_string + '%'  # set text
                            self.obdengineloadval = response_Load_int_adjusted #value, for progress bar

    def build(self):
        global developermode
        KVFILE = Builder.load_file("main.kv")
        global root
        root = ROOT()

        Clock.schedule_interval(self.updatetime, .1)
        Clock.schedule_interval(self.updatedate, 1)
        Clock.schedule_interval(self.updatetemp, 1)
        Clock.schedule_interval(self.updatevariables, .104556) #weird number to get RPi stopwatch as close as possible - found through testing
        Clock.schedule_interval(self.updatemessage, 1)
        Clock.schedule_interval(self.updateaccel, .1)
        if developermode == 1:
            Clock.schedule_interval(self.updateOBDdata, .01)
        else:
            Clock.schedule_interval(self.updateOBDdata, .1)

        #add the widgets
        
        root.add_widget(KVFILE) #adds the main GUI
        return root

#Some KivyMD Stuff
    def show_easter_dialog(self):
        content = MDLabel(font_style='Body1',
                          theme_text_color='Secondary',
                          text="Congrats! You found this easter egg!\n\n"
                               "Thanks for trying out CoPilot!  :)",
                          valign='top')

        content.bind(size=content.setter('text_size'))
        self.dialog = MDDialog(title="Easter Egg!",
                               content=content,
                               size_hint=(.8, None),
                               height=dp(200),
                               auto_dismiss=False)

        self.dialog.add_action_button("Dismiss",
                                      action=lambda *x: self.dialog.dismiss())
        self.dialog.open()

    def show_indev_dialog(self):
        content = MDLabel(font_style='Body1',
                          theme_text_color='Secondary',
                          text="This feature is currently in development.\n\n"
                               "Thanks for trying out CoPilot!  :)",
                          valign='top')

        content.bind(size=content.setter('text_size'))
        self.dialog = MDDialog(title="Coming soon!",
                               content=content,
                               size_hint=(.8, None),
                               height=dp(200),
                               auto_dismiss=False)

        self.dialog.add_action_button("Dismiss",
                                      action=lambda *x: self.dialog.dismiss())
        self.dialog.open()

    def show_version_dialog(self):
        content = MDLabel(font_style='Body1',
                          theme_text_color='Secondary',
                          text="Created by Joel Zeller\n\n"
                               "Please send any bugs to joelzeller25@hotmail.com",
                          valign='top')

        content.bind(size=content.setter('text_size'))
        self.dialog = MDDialog(title="CoPilot "+version,
                               content=content,
                               size_hint=(.8, None),
                               height=dp(200),
                               auto_dismiss=False)

        self.dialog.add_action_button("Dismiss",
                                      action=lambda *x: self.dialog.dismiss())
        self.dialog.open()

    def show_example_snackbar(self, snack_type):
        if devtaps == 4:
            if snack_type == 'enabledev':
                Snackbar.make("Developer Mode Enabled")
        # elif snack_type == 'button':
        #     Snackbar.make("This is a snackbar", button_text="with a button!",
        #                   button_callback=lambda *args: 2)
        # elif snack_type == 'verylong':
        #     Snackbar.make("This is a very very very very very very very long "
        #                   "snackbar!",
        #                   button_text="Hello world")


#SCHEDUALING

        #AUDIO

    def bluetoothplay_callback_schedge(obj):
        if BLUETOOTHON == 1:
            try:
                os.system('dbus-send --system --type=method_call --dest=org.bluez /org/bluez/hci0/dev_'+bluetoothdevicemac+'/player0 org.bluez.MediaPlayer1.Play')
            except:
                print "can't play"

    def bluetoothpause_callback_schedge(obj):
        if BLUETOOTHON == 1:
            try:
                os.system('dbus-send --system --type=method_call --dest=org.bluez /org/bluez/hci0/dev_'+bluetoothdevicemac+'/player0 org.bluez.MediaPlayer1.Pause')
            except:
                print "can't pause"

    def seekup_callback_schedge(obj):
        if BLUETOOTHON == 0:
            Clock.schedule_once(seekup_callback)
            Clock.schedule_once(seekup_callback, 0.1) #on for .1 secs, then off again
        if BLUETOOTHON == 1:
            try:
                os.system('dbus-send --system --type=method_call --dest=org.bluez /org/bluez/hci0/dev_'+bluetoothdevicemac+'/player0 org.bluez.MediaPlayer1.Next')
            except:
                print "can't next"

    def seekdown_callback_schedge(obj):
        if BLUETOOTHON == 0:
            Clock.schedule_once(seekdown_callback)
            Clock.schedule_once(seekdown_callback, 0.1) #on for .1 secs, then off again
        if BLUETOOTHON == 1:
            try:
                os.system('dbus-send --system --type=method_call --dest=org.bluez /org/bluez/hci0/dev_'+bluetoothdevicemac+'/player0 org.bluez.MediaPlayer1.Previous')
            except:
                print "can't prev"

    def aux_callback_schedge(obj):
        Clock.schedule_once(aux_callback)
        Clock.schedule_once(aux_callback, 0.1) #on for .1 secs, then off again

    def amfm_callback_schedge(obj):
        Clock.schedule_once(amfm_callback) 
        Clock.schedule_once(amfm_callback, 0.1) #on for .1 secs, then off again

    def enablebluetooth(obj):
        global BLUETOOTHON
        BLUETOOTHON = 1

    def disablebluetooth(obj):
        global BLUETOOTHON
        BLUETOOTHON = 0

    def displaybtdata(obj):
        global DISPLAYBTDATA
        DISPLAYBTDATA = 1
        global animation_start_time
        animation_start_time = int(float(time_second_mod))  # sets a reference time for animations

    def killbtdata(obj):
        global DISPLAYBTDATA
        DISPLAYBTDATA = 0

        #CONTROLS

    def garage_callback_schedge(obj):
        Clock.schedule_once(garage_callback) #called once - setup to only activate when button is down

    def radar_callback_schedge(obj):
        Clock.schedule_once(radar_callback) #called once so next press alternates status

    def leds_callback_schedge(obj):
        Clock.schedule_once(leds_callback) #called once so next press alternates status

    def windowsup_callback_schedge(obj):
        global WINDOWSUPON
        global WINDOWSDOWNON
        if WINDOWSDOWNON == 0: #only works when windows down isnt running
            Clock.schedule_once(windowsup_callback) #called once so next press alternates status
            Clock.schedule_once(windowsupOFF_callback, windowuptime) #on for set x secs, then off again - time needs edited
            return
        if WINDOWSUPON == 1:
            Clock.schedule_once(windowsupOFF_callback) #if windows going up while pushed, will cancel and stop windows

    def windowsdown_callback_schedge(obj):
        global WINDOWSUPON
        global WINDOWSDOWNON
        if WINDOWSUPON == 0: #only works when windows up isnt running
            Clock.schedule_once(windowsdown_callback) #called once so next press alternates status
            Clock.schedule_once(windowsdownOFF_callback, windowdowntime) #on for set x secs, then off again - time needs edited
            return
        if WINDOWSDOWNON == 1:
            Clock.schedule_once(windowsdownOFF_callback) #if windows going down while pushed, will cancel and stop windows

    # following 6 functions serve purpose to debug windows
    def driverup_callback_schedge(obj):
        Clock.schedule_once(driverup_callback) #called once - setup to only activate when button is down
    def driverstop_callback_schedge(obj):
        Clock.schedule_once(driverstop_callback) #called once - setup to only activate when button is down
    def driverdown_callback_schedge(obj):
        Clock.schedule_once(driverdown_callback) #called once - setup to only activate when button is down
    def passengerup_callback_schedge(obj):
        Clock.schedule_once(passengerup_callback) #called once - setup to only activate when button is down
    def passengerstop_callback_schedge(obj):
        Clock.schedule_once(passengerstop_callback) #called once - setup to only activate when button is down
    def passengerdown_callback_schedge(obj):
        Clock.schedule_once(passengerdown_callback) #called once - setup to only activate when button is down
    def allwindowsstop_callback_schedge(obj):
        Clock.schedule_once(allwindowsstop_callback) #called once - setup to only activate when button is down

#VARIBLE SETTINGS
    def add_launch(obj): #use on_release: app.add_launchanalog() to call - used to create the lights on the xmas tree drag lights
        global time_second_mod
        global launch_start_time
        launch_start_time = int(float(time_second_mod)) #sets a reference time for launch control timing

    #messages
    def kill_message(obj): #use on_release: app.kill_message() to call
        global message
        message = 0
        
    def add_message(obj): #use on_release: app.add_message() to call
        global message
        message = 1

    #stopwatch button functions
    def stopwatch_start(obj): #use on_release: app.stopwatch_start() to call
        global swactive
        swactive = 1
    def stopwatch_stop(obj): #use on_release: app.stopwatch_start() to call
        global swactive
        swactive = 0
    def stopwatch_reset(obj): #use on_release: app.stopwatch_start() to call
        global swactive
        global swminute
        global swsecond
        global swtenth
        swactive = 0
        swminute = 0
        swsecond = 0
        swtenth = 0

    #hot key 1 settings functions
    def sethotkey1_SeekUp(obj):
        global hotkey1string
        hotkey1string = "Seek Up"
    def sethotkey1_SeekDown(obj):
        global hotkey1string
        hotkey1string = "Seek Down"
    def sethotkey1_Garage(obj):
        global hotkey1string
        hotkey1string = "Garage"
    def sethotkey1_Radar(obj):
        global hotkey1string
        hotkey1string = "Radar"
    def sethotkey1_CupLights(obj):
        global hotkey1string
        hotkey1string = "Cup Lights"
    def sethotkey1_WindowsUp(obj):
        global hotkey1string
        hotkey1string = "Windows Up"
    def sethotkey1_WindowsDown(obj):
        global hotkey1string
        hotkey1string = "Windows Down"
    def sethotkey1_ScreenToggle(obj):
        global hotkey1string
        hotkey1string = "Screen Toggle"
    def sethotkey1_None(obj):
        global hotkey1string
        hotkey1string = "None"

    #hot key 2 settings functions
    def sethotkey2_SeekUp(obj):
        global hotkey2string
        hotkey2string = "Seek Up"
    def sethotkey2_SeekDown(obj):
        global hotkey2string
        hotkey2string = "Seek Down"
    def sethotkey2_Garage(obj):
        global hotkey2string
        hotkey2string = "Garage"
    def sethotkey2_Radar(obj):
        global hotkey2string
        hotkey2string = "Radar"
    def sethotkey2_CupLights(obj):
        global hotkey2string
        hotkey2string = "Cup Lights"
    def sethotkey2_WindowsUp(obj):
        global hotkey2string
        hotkey2string = "Windows Up"
    def sethotkey2_WindowsDown(obj):
        global hotkey2string
        hotkey2string = "Windows Down"
    def sethotkey2_ScreenToggle(obj):
        global hotkey2string
        hotkey2string = "Screen Toggle"
    def sethotkey2_None(obj):
        global hotkey2string
        hotkey2string = "None"

    def sethotkeydefaults(obj):
        global hotkey1string
        global hotkey2string
        hotkey1string = "None"
        hotkey2string = "None"


    def setwallpaper0(obj):
        global wallpaper
        wallpaper = 0

    def setwallpaper1(obj):
        global wallpaper
        wallpaper = 1

    def setwallpaper2(obj):
        global wallpaper
        wallpaper = 2

    def setwallpaper3(obj):
        global wallpaper
        wallpaper = 3

    def setwallpaper4(obj):
        global wallpaper
        wallpaper = 4

    def setwallpaper5(obj):
        global wallpaper
        wallpaper = 5

    def setwallpaper6(obj):
        global wallpaper
        wallpaper = 6

    def setwallpaper7(obj):
        global wallpaper
        wallpaper = 7

    def setwallpaper8(obj):
        global wallpaper
        wallpaper = 8

    def setwallpaper9(obj):
        global wallpaper
        wallpaper = 9

    def setwallpaper10(obj):
        global wallpaper
        wallpaper = 10

    def setwallpaper11(obj):
        global wallpaper
        wallpaper = 11

    def setwallpaper12(obj):
        global wallpaper
        wallpaper = 12

    def setwallpaper13(obj):
        global wallpaper
        wallpaper = 13

    def setwallpaper14(obj):
        global wallpaper
        wallpaper = 14

    def setwallpaper15(obj):
        global wallpaper
        wallpaper = 15

    def setwallpaper16(obj):
        global wallpaper
        wallpaper = 16

    def setwallpaper17(obj):
        global wallpaper
        wallpaper = 17

    def setwallpaper18(obj):
        global wallpaper
        wallpaper = 18

    def setwallpaper19(obj):
        global wallpaper
        wallpaper = 19

    def setwallpaper20(obj):
        global wallpaper
        wallpaper = 20

    def setwallpaper21(obj):
        global wallpaper
        wallpaper = 21

    def setwallpaper22(obj):
        global wallpaper
        wallpaper = 22

    def setwallpaper23(obj):
        global wallpaper
        wallpaper = 23

    def setwallpaper24(obj):
        global wallpaper
        wallpaper = 24

    def setwallpaper25(obj):
        global wallpaper
        wallpaper = 25

    def setwallpaper26(obj):
        global wallpaper
        wallpaper = 26

    def setwallpaper27(obj):
        global wallpaper
        wallpaper = 27

    def setwallpaper28(obj):
        global wallpaper
        wallpaper = 28

    def devtap(obj):
        global devtaps
        global developermode
        if devtaps < 4:
            devtaps = devtaps + 1
        if devtaps == 5:            # five taps on the settings title will enter dev mode
            developermode = 1

    def killdev(obj):
        global devtaps
        global developermode
        developermode = 0
        devtaps = 0

    def save(obj):
        # save new varibles for next boot
        global theme
        global wallpaper
        global hotkey1string
        global hotkey2string
        global oildatemonth
        global oildateday
        global oildateyear
        global oilmileage
        global oilnotify
        global speedlimit
        global rpmredline
        wallpaper = str(wallpaper)
        oildatemonth = str(oildatemonth)
        oildateday = str(oildateday)
        oildateyear = str(oildateyear)
        oilmileage = str(oilmileage)
        oilnotify = str(oilnotify)
        speedlimit = str(int(speedlimit))
        rpmredline = str(int(rpmredline))
        f = open('savedata.txt', 'r+')
        f.truncate() # wipe everything
        f.write(theme + "\n" + wallpaper + "\n" + hotkey1string + "\n" + hotkey2string + "\n" + oildatemonth + "\n" + oildateday + "\n" + oildateyear + "\n" + oilmileage + "\n" + oilnotify + "\n" + speedlimit + "\n" + rpmredline)
        f.close()
        oildatemonth = int(oildatemonth)
        oildateday = int(oildateday)
        oildateyear = int(oildateyear)
        oilmileage = int(oilmileage)
        oilnotify = int(oilnotify)
        speedlimit = int(speedlimit)
        rpmredline = int(rpmredline)

    def shutdown(obj):
        # save new varibles for next boot
        global theme
        global wallpaper
        global hotkey1string
        global hotkey2string
        global oildatemonth
        global oildateday
        global oildateyear
        global oilmileage
        global oilnotify
        global speedlimit
        global rpmredline
        wallpaper = str(wallpaper)
        oildatemonth = str(oildatemonth)
        oildateday = str(oildateday)
        oildateyear = str(oildateyear)
        oilmileage = str(oilmileage)
        oilnotify = str(oilnotify)
        speedlimit = str(int(speedlimit))
        rpmredline = str(int(rpmredline))
        f = open('savedata.txt', 'r+')
        f.truncate() # wipe everything
        f.write(theme + "\n" + wallpaper + "\n" + hotkey1string + "\n" + hotkey2string + "\n" + oildatemonth + "\n" + oildateday + "\n" + oildateyear + "\n" + oilmileage + "\n" + oilnotify + "\n" + speedlimit + "\n" + rpmredline)
        f.close()
        oildatemonth = int(oildatemonth)
        oildateday = int(oildateday)
        oildateyear = int(oildateyear)
        oilmileage = int(oilmileage)
        oilnotify = int(oilnotify)
        speedlimit = int(speedlimit)
        rpmredline = int(rpmredline)

        # turn off screen and shutdown
        os.system("sudo echo 1 > /sys/class/backlight/rpi_backlight/bl_power") #turns screen off
        os.system("sudo shutdown -h now")

    def reboot(obj):
        # save new varibles for next boot
        global theme
        global wallpaper
        global hotkey1string
        global hotkey2string
        global oildatemonth
        global oildateday
        global oildateyear
        global oilmileage
        global oilnotify
        global speedlimit
        global rpmredline
        wallpaper = str(wallpaper)
        oildatemonth = str(oildatemonth)
        oildateday = str(oildateday)
        oildateyear = str(oildateyear)
        oilmileage = str(oilmileage)
        speedlimit = str(int(speedlimit))
        rpmredline = str(int(rpmredline))
        f = open('savedata.txt', 'r+')
        f.truncate()
        f.write(theme + "\n" + wallpaper + "\n" + hotkey1string + "\n" + hotkey2string + "\n" + oildatemonth + "\n" + oildateday + "\n" + oildateyear + "\n" + oilmileage + "\n" + oilnotify + "\n" + speedlimit + "\n" + rpmredline)
        f.close()
        oildatemonth = int(oildatemonth)
        oildateday = int(oildateday)
        oildateyear = int(oildateyear)
        oilmileage = int(oilmileage)
        oilnotify = int(oilnotify)
        speedlimit = int(speedlimit)
        rpmredline = int(rpmredline)

        os.system("sudo reboot")

    def TurnScreenOn(obj):
        global screenon
        screenon = 1
        os.system("sudo echo 0 > /sys/class/backlight/rpi_backlight/bl_power") #turns screen on

    def TurnScreenOff(obj):
        global screenon
        screenon = 0
        os.system("sudo echo 1 > /sys/class/backlight/rpi_backlight/bl_power") #turns screen off


    #brightness control functions
    def BrightnessSetLock(obj): #only for lockscreen - not used yet
        os.system("sudo echo 15 > /sys/class/backlight/rpi_backlight/brightness") #sets screen brightness to ~ 1%
    def BrightnessSet1(obj):
        os.system("sudo echo 15 > /sys/class/backlight/rpi_backlight/brightness") #sets screen brightness to ~ 10%
    def BrightnessSet2(obj):
        os.system("sudo echo 60 > /sys/class/backlight/rpi_backlight/brightness") #sets screen brightness to ~ 25%
    def BrightnessSet3(obj):
        os.system("sudo echo 80 > /sys/class/backlight/rpi_backlight/brightness") #sets screen brightness to ~ 50%
    def BrightnessSet4(obj):
        os.system("sudo echo 120 > /sys/class/backlight/rpi_backlight/brightness") #sets screen brightness to ~ 75%
    def BrightnessSet5(obj):
        os.system("sudo echo 175 > /sys/class/backlight/rpi_backlight/brightness") #sets screen brightness to ~ 100%

    def killtemp(obj): #used to kill the temp label when on screens other than main
        global TEMPON
        TEMPON = 0

    def addtemp(obj): #used to kill the temp label when on screens other than main
        global TEMPON
        global animation_start_time
        TEMPON = 1
        animation_start_time = int(float(time_second_mod)) #sets a reference time for animations

    def killaccel(obj):
        global ACCELON
        ACCELON = 0

    def addaccel(obj):
        global ACCELON
        ACCELON = 1

    def connect_OBD(obj): #sets value to one so connection code only runs once
        global OBDconnection
        if developermode == 0:
            OBDconnection = 1

    def kill_OBDVAR(obj): #used to kill the OBD label when on screens other than main
        global OBDVAR
        global devobd
        devobd = 0
        OBDVAR = 0

    def add_OBDVAR_SPEED(obj): #used to change the OBD label to other types of data
        global OBDVAR
        global time_second_mod
        global animation_start_time
        OBDVAR = 1
        animation_start_time = int(float(time_second_mod)) #sets a reference time for animations
        
    def add_OBDVAR_RPM(obj): #used to change the OBD label to other types of data
        global OBDVAR
        global time_second_mod
        global animation_start_time
        OBDVAR = 2
        animation_start_time = int(float(time_second_mod)) #sets a reference time for animations

    def zero_RPMmax(obj): #zeros out RPM max
        global maxRPM
        maxRPM = 0

    def redline_value(self, instance, value): #function that is updated when redline slider is moved
        global rpmredline
        rpmredline = value

    def speedlimit_value(self, instance, value): #function that is updated when speed limit slider is moved
        global speedlimit
        speedlimit = value

    def add_OBDVAR_COOLANT_TEMP(obj): #used to change the OBD label to other types of data
        global OBDVAR
        global time_second_mod
        global animation_start_time
        OBDVAR = 4
        animation_start_time = int(float(time_second_mod)) #sets a reference time for animations
    def add_OBDVAR_INTAKE_TEMP(obj): #used to change the OBD label to other types of data
        global OBDVAR
        global time_second_mod
        global animation_start_time
        OBDVAR = 5
        animation_start_time = int(float(time_second_mod)) #sets a reference time for animations
    def add_OBDVAR_LOAD(obj): #used to change the OBD label to other types of data
        global OBDVAR
        global time_second_mod
        global animation_start_time
        OBDVAR = 6
        animation_start_time = int(float(time_second_mod)) #sets a reference time for animations

    #_________________________________________________________________

    #Function to setup OBD stuff
    def setup_OBD(obj):
        if developermode == 0:
            global connection
            global cmd_RPM
            global cmd_SPEED
            global cmd_CoolantTemp
            global cmd_IntakeTemp
            global cmd_Load
            global OBDconnection

            if OBDconnection == 0:

                os.system('sudo rfcomm bind /dev/rfcomm1 00:1D:A5:16:3E:ED')
                connection = obd.OBD() # auto-connects to USB or RF port

                cmd_RPM = obd.commands.RPM # select RPM OBD command (sensor)
                cmd_SPEED = obd.commands.SPEED # select SPEED OBD command (sensor)
                cmd_CoolantTemp = obd.commands.COOLANT_TEMP # select CoolantTemp OBD command (sensor)
                cmd_IntakeTemp = obd.commands.INTAKE_TEMP # select IntakeTemp OBD command (sensor)
                cmd_Load = obd.commands.ENGINE_LOAD # select EngineLoad OBD command (sensor)

    def oilmileageup100(obj):
        global oilmileage
        oilmileage = oilmileage+100
    def oilmileagedown100(obj):
        global oilmileage
        oilmileage = oilmileage-100
    def oilmileageup1k(obj):
        global oilmileage
        oilmileage = oilmileage+1000
    def oilmileagedown1k(obj):
        global oilmileage
        oilmileage = oilmileage-1000
    def oilmileageup10k(obj):
        global oilmileage
        oilmileage = oilmileage+10000
    def oilmileagedown10k(obj):
        global oilmileage
        oilmileage = oilmileage-10000
    def oilmileageup100k(obj):
        global oilmileage
        oilmileage = oilmileage+100000
    def oilmileagedown100k(obj):
        global oilmileage
        oilmileage = oilmileage-100000

    def oildatemonthup(obj):
        global oildatemonth
        if oildatemonth < 12:
            oildatemonth = oildatemonth+1
        else:
            oildatemonth = 1
    def oildatemonthdown(obj):
        global oildatemonth
        if oildatemonth > 1:
            oildatemonth = oildatemonth-1
        else:
            oildatemonth = 12
    def oildatedayup(obj):
        global oildateday
        if oildateday < 31:
            oildateday = oildateday+1
        else:
            oildateday = 1
    def oildatedaydown(obj):
        global oildateday
        if oildateday > 1:
            oildateday = oildateday-1
        else:
            oildateday = 31
    def oildateyearup(obj):
        global oildateyear
        oildateyear = oildateyear+1
    def oildateyeardown(obj):
        global oildateyear
        oildateyear = oildateyear-1
    def oilnotifyflip(obj):
        global oilnotify
        if oilnotify == 1:
            oilnotify = 0
            return
        if oilnotify == 0:
            oilnotify = 1

#____________________________________________________________________
#GPIO CALLBACKS
def seekup_callback(obj): #logic for seekup gpio
    global SEEKUPON
    if SEEKUPON == 0:
        if developermode == 0:
            GPIO.output(seekupPin, GPIO.LOW)
        SEEKUPON = 1
    else:
        if developermode == 0:
            GPIO.output(seekupPin, GPIO.HIGH)
        SEEKUPON = 0

def seekdown_callback(obj): #logic for seekdown gpio
    global SEEKDOWNON
    if SEEKDOWNON == 0:
        if developermode == 0:
            GPIO.output(seekdownPin, GPIO.LOW)
        SEEKDOWNON = 1
    else:
        if developermode == 0:
            GPIO.output(seekdownPin, GPIO.HIGH)
        SEEKDOWNON = 0

def aux_callback(obj): #logic for aux gpio
    global AUXON
    if AUXON == 0:
        if developermode == 0:
            GPIO.output(auxPin, GPIO.LOW)
        AUXON = 1
    else:
        if developermode == 0:
            GPIO.output(auxPin, GPIO.HIGH)
        AUXON = 0

def amfm_callback(obj): #logic for amfm gpio
    global AMFMON
    if AMFMON == 0:
        if developermode == 0:
            GPIO.output(amfmPin, GPIO.LOW)
        AMFMON = 1
    else:
        if developermode == 0:
            GPIO.output(amfmPin, GPIO.HIGH)
        AMFMON = 0

        #CONTROLS

def garage_callback(obj): #logic for garage gpio
    global GARAGEON
    if GARAGEON == 0:
        if developermode == 0:
            GPIO.output(garagePin, GPIO.LOW)
        GARAGEON = 1
    else:
        if developermode == 0:
            GPIO.output(garagePin, GPIO.HIGH)
        GARAGEON = 0

def radar_callback(obj): #logic for radar gpio
    global RADARON
    if RADARON == 0:
        if developermode == 0:
            GPIO.output(radarPin, GPIO.LOW)
        RADARON = 1
    else:
        if developermode == 0:
            GPIO.output(radarPin, GPIO.HIGH)
        RADARON = 0

def leds_callback(obj): #logic for cup holder leds gpio
    global LEDSON
    if LEDSON == 0:
        if developermode == 0:
            GPIO.output(ledsPin, GPIO.HIGH)
        LEDSON = 1
    else:
        if developermode == 0:
            GPIO.output(ledsPin, GPIO.LOW)
        LEDSON = 0

def windowsup_callback(obj): #logic for windows up gpio
    global WINDOWSUPON
    global WINDOWSDOWNON
    
    if WINDOWSDOWNON == 0:
        
        if WINDOWSUPON == 0:
            if developermode == 0:
                GPIO.output(driverwindowupPin, GPIO.LOW)
                GPIO.output(passwindowupPin, GPIO.LOW)
            WINDOWSUPON = 1
            return
        if WINDOWSUPON == 1:
            if developermode == 0:
                GPIO.output(driverwindowupPin, GPIO.HIGH)
                GPIO.output(passwindowupPin, GPIO.HIGH)
            WINDOWSUPON = 0
            return

        
def windowsupOFF_callback(obj): #logic to halt the windows
    global WINDOWSUPON
    global WINDOWSDOWNON
    WINDOWSUPON = 0
    if developermode == 0:
        GPIO.output(driverwindowupPin, GPIO.HIGH)
        GPIO.output(passwindowupPin, GPIO.HIGH)

def windowsdown_callback(obj): #logic for windows down gpio
    global WINDOWSDOWNON
    global WINDOWSUPON
    
    if WINDOWSUPON == 0:
        
        if WINDOWSDOWNON == 0:
            if developermode == 0:
                GPIO.output(driverwindowdownPin, GPIO.LOW)
                GPIO.output(passwindowdownPin, GPIO.LOW)
            WINDOWSDOWNON = 1
            return
        if WINDOWSDOWNON == 1:
            if developermode == 0:
                GPIO.output(driverwindowdownPin, GPIO.HIGH)
                GPIO.output(passwindowdownPin, GPIO.HIGH)
            WINDOWSDOWNON = 0
            return

def windowsdownOFF_callback(obj): #logic to halt the windows
    global WINDOWSDOWNON
    global WINDOWSUPON
    WINDOWSDOWNON = 0
    if developermode == 0:
        GPIO.output(driverwindowdownPin, GPIO.HIGH)
        GPIO.output(passwindowdownPin, GPIO.HIGH)

    # callback functions for window debugging

def driverup_callback(obj): #logic for driver up gpio
    global DRIVERUPON
    if DRIVERUPON == 0:
        if developermode == 0:
            GPIO.output(driverwindowupPin, GPIO.LOW)
        DRIVERUPON = 1
    else:
        if developermode == 0:
            GPIO.output(driverwindowupPin, GPIO.HIGH)
        DRIVERUPON = 0

def driverstop_callback(obj): #logic for driver window emergency stop
    global WINDOWSDOWNON
    global WINDOWSUPON
    WINDOWSDOWNON = 0
    WINDOWSUPON = 0
    if developermode == 0:
        GPIO.output(driverwindowupPin, GPIO.HIGH)
        GPIO.output(driverwindowdownPin, GPIO.HIGH)

def driverdown_callback(obj): #logic for driver down gpio
    global DRIVERDOWNON
    if DRIVERDOWNON == 0:
        if developermode == 0:
            GPIO.output(driverwindowdownPin, GPIO.LOW)
        DRIVERDOWNON = 1
    else:
        if developermode == 0:
            GPIO.output(driverwindowdownPin, GPIO.HIGH)
        DRIVERDOWNON = 0

def passengerup_callback(obj): #logic for passenger up gpio
    global PASSENGERUPON
    if PASSENGERUPON == 0:
        if developermode == 0:
            GPIO.output(passwindowupPin, GPIO.LOW)
        PASSENGERUPON = 1
    else:
        if developermode == 0:
            GPIO.output(passwindowupPin, GPIO.HIGH)
        PASSENGERUPON = 0

def passengerstop_callback(obj): #logic for passenger window emergency stop
    global WINDOWSDOWNON
    global WINDOWSUPON
    WINDOWSDOWNON = 0
    WINDOWSUPON = 0
    if developermode == 0:
        GPIO.output(passwindowupPin, GPIO.HIGH)
        GPIO.output(passwindowdownPin, GPIO.HIGH)

def passengerdown_callback(obj): #logic for passenger down gpio
    global PASSENGERDOWNON
    if PASSENGERDOWNON == 0:
        if developermode == 0:
            GPIO.output(passwindowdownPin, GPIO.LOW)
            GPIO.output(passwindowdownPin, GPIO.LOW)
        PASSENGERDOWNON = 1
    else:
        if developermode == 0:
            GPIO.output(passwindowdownPin, GPIO.HIGH)
        PASSENGERDOWNON = 0

def allwindowsstop_callback(obj): #logic for all windows emergency stop
    global WINDOWSDOWNON
    global WINDOWSUPON
    WINDOWSDOWNON = 0
    WINDOWSUPON = 0
    if developermode == 0:
        GPIO.output(passwindowupPin, GPIO.HIGH)
        GPIO.output(passwindowdownPin, GPIO.HIGH)
        GPIO.output(driverwindowupPin, GPIO.HIGH)
        GPIO.output(driverwindowdownPin, GPIO.HIGH)

if __name__ =='__main__':
    MainApp().run()