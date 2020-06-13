import kivy
#kivy.require('1.0.6')
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, SlideTransition
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.theming import ThemeManager
import threading
import subprocess
import socket
import datetime
import time
import os
import math

# Program Info
# ---------------------------------------------------------------------------------------------------------------------------------------------
globalversion = "V0.1.0"
# 6/12/2020
# Created by Joel Zeller

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Configuration Variables
developermode = 1           # set to 1 to disable all GPIO, temp probe, and obd stuff
externalshutdown = 0        # set to 1 if you have an external shutdown circuit applied - High = Awake, Low = Shutdown
AccelPresent = 0            # set to 1 if adxl345 accelerometer is present
RGBEnabled = 0              # set to 1 if you have RGBs wired in
OBDPresent = 1              # set to 1 if you have an OBD connection with the vehicle
onPi = 1                    # 1 by default, will change to 0 if code cannot import GPIO from Pi
autobrightness = 2          # AutoBrightness on Boot #set to 1 if you have the newer RPi display and want autobrightness
                                # set to 0 if you do not or do not want autobrightness
                                # adjust to suit your needs :)
                            # Set to 2 for auto dim on boot every time (use main screen full screen button to toggle full dim and full bright)

# ---------------------------------------------------------------------------------------------------------------------------------------------
# For PC dev work
from kivy.config import Config
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '480')
from kivy.core.window import Window
Window.size = (800, 480)

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Inital Setup functions
try:
    import RPi.GPIO as GPIO
    onPi = 1  # If GPIO is successfully imported, we can assume we are running on a Raspberry Pi
    import obd
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    if externalshutdown == 1:
        GPIO.setup(21, GPIO.IN)  # setup GPIO pin #21 as external shutdown pin
except:
    onPi = 0
    OBDPresent = 0
    RGBEnabled = 0
    externalshutdown = 0
    print("This is not being run on a Raspberry Pi. Functionality is limited.")

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Auto Shutdown Code
def CheckExternalShutdown():
    while True:
        if GPIO.input(21) == 0:  # if port 21 == 0, M0 will drive LOW when time to shutdown
            print ("GPIO 21 is low - Start Shutdown Sequence")
            time.sleep(5)  # wait 5 seconds to check again
            if GPIO.input(21) == 0:
                print ("Passed 5 second check")
                sys.shutdownflag = 1  # set shutdown flag so kv file can show shutdown screen
                time.sleep(2)  # wait 2 more seconds to double check it
                if GPIO.input(21) == 0:
                    print ("Pi is shutting down now, it is irreversible")

                    time.sleep(5)  # show the shutdown screen for 5 seconds longer
                    print ("SHUTDOWN SENT")
                    os.system("sudo echo 1 > /sys/class/backlight/rpi_backlight/bl_power")  # turns screen off
                    time.sleep(1)
                    os.system("sudo shutdown -h now")
            else:
                print ("Shutdown signal <5 seconds, keep ON")
        sys.shutdownflag = 0  # set shutdown flag so kv file can go back to normal
        time.sleep(.5)

if externalshutdown == 1:
    ExternalShutdownCheckThread = threading.Thread(name='check_externalshutdown_thread', target=CheckExternalShutdown)
    ExternalShutdownCheckThread.start()

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Initialize Classes and Variables and a few threads
class sys:
    version = globalversion
    ip = "No IP address found..."
    ssid = "No SSID found..."
    CPUTemp = 0
    CPUVolts = 0
    getsysteminfo = False
    screen = 1
    brightness = 0
    shutdownflag = 0
    TempUnit = "F"
    SpeedUnit = "MPH"

    def setbrightness(self, value):
        sys.brightness = value
        brightset = "sudo echo " + str(sys.brightness) + " > /sys/class/backlight/rpi_backlight/brightness"
        os.system(brightset)

    def loaddata(self):
        f = open('savedata.txt', 'r+')  # read from text file
        #Mode = f.readline()
        RGB.Mode = f.readline().rstrip()
        RGB.DC_R_DR = int(f.readline())
        RGB.DC_G_DR = int(f.readline())
        RGB.DC_B_DR = int(f.readline())
        RGB.DC_R_AS = int(f.readline())
        RGB.DC_G_AS = int(f.readline())
        RGB.DC_B_AS = int(f.readline())
        OBD.warning.RPM = int(f.readline())
        OBD.warning.Speed = int(f.readline())
        OBD.warning.CoolantTemp = int(f.readline())
        OBD.warning.IntakeTemp = int(f.readline())
        OBD.warning.LTFT = int(f.readline())
        OBD.warning.STFT = int(f.readline())
        OBD.warning.CatTemp = int(f.readline())
        sys.Fahrenheit = f.readline().rstrip()
        sys.MPH = f.readline().rstrip()
        f.close()

    def savedata(self):
        f = open('savedata.txt', 'r+')
        f.truncate()  # wipe everything
        f.write(
            RGB.Mode + "\n" +
            str(RGB.DC_R_DR) + "\n" +
            str(RGB.DC_G_DR) + "\n" +
            str(RGB.DC_B_DR) + "\n" +
            str(RGB.DC_R_AS) + "\n" +
            str(RGB.DC_G_AS) + "\n" +
            str(RGB.DC_B_AS) + "\n" +
            str(OBD.warning.RPM) + "\n" +
            str(OBD.warning.Speed) + "\n" +
            str(OBD.warning.CoolantTemp) + "\n" +
            str(OBD.warning.IntakeTemp) + "\n" +
            str(OBD.warning.LTFT) + "\n" +
            str(OBD.warning.STFT) + "\n" +
            str(OBD.warning.CatTemp) + "\n" +
            sys.TempUnit + "\n" +
            sys.SpeedUnit
        )
        f.close()

class OBD:
    Connected = 0  # connection is off by default - will be turned on in setup thread
    RPM_max = 0    # init all values to 0
    Speed_max = 0
    RPM = 0
    Speed = 0
    CoolantTemp = 0
    CoolantTemp_ForBar = 0
    IntakeTemp = 0
    IntakePressure = 0
    Load = 0
    ThrottlePos = 0
    LTFT = 0
    STFT = 0
    TimingAdv = 0
    MAF = 0
    RunTime = 0
    FuelLevel = 0
    WarmUpsSinceDTC = 0
    DistanceSinceDTC = 0
    CatTemp = 0

    class dev:  # used for development of GUI and testing
        Speed = 0
        Speed_max = 0
        Speed_inc = 1
        RPM = 0
        RPM_max = 0
        RPM_inc = 1
        CoolantTemp = 0
        CoolantTemp_inc = 1
        CoolantTemp_ForBar = 0
        FuelTrim = 0
        FuelTrim_inc = 1
        Generic = 0
        Generic_inc = 1

    class enable:  # used to turn on and off OBD cmds to speed up communication
        RPM = 0
        Speed = 0
        CoolantTemp = 1  # On Start-Up Screen
        IntakeTemp = 1  # On Start-Up Screen
        IntakePressure = 0
        Load = 0
        ThrottlePos = 0
        LTFT = 1  # On Start-Up Screen
        STFT = 1  # On Start-Up Screen
        TimingAdv = 1  # On Start-Up Screen
        MAF = 0
        RunTime = 0
        FuelLevel = 0
        WarmUpsSinceDTC = 0
        DistanceSinceDTC = 0
        CatTemp = 1  # On Start-Up Screen

    class warning:  # used to show warning when value is met, these will be read from savefile
        RPM = 0
        Speed = 0
        CoolantTemp = 0
        IntakeTemp = 0
        LTFT = 0
        STFT = 0
        CatTemp = 0

    # Thread functions - to be called later
    # These will run in the background and will not block the GUI
    def OBD_setup_thread(self):
        try:
            # os.system('sudo rfcomm bind /dev/rfcomm1 00:1D:A5:16:3E:ED')  #Blue Adapter
            os.system('sudo rfcomm bind /dev/rfcomm1 00:17:E9:60:7C:BC')  # Hondata
            # os.system('sudo rfcomm bind /dev/rfcomm1 00:04:3E:4B:07:66') #Green LXLink
        except:
            print ("Failed to initialize OBDII - device may already be connected.")
        time.sleep(2)
        print ("Bluetooth Connected")
        try:
            OBD.connection = obd.OBD()  # auto-connects to USB or RF port
            OBD.cmd_RPM = obd.commands.RPM
            OBD.cmd_Speed = obd.commands.SPEED
            OBD.cmd_CoolantTemp = obd.commands.COOLANT_TEMP
            OBD.cmd_IntakeTemp = obd.commands.INTAKE_TEMP
            OBD.cmd_IntakePressure = obd.commands.INTAKE_PRESSURE
            OBD.cmd_Load = obd.commands.ENGINE_LOAD
            OBD.cmd_ThrottlePos = obd.commands.THROTTLE_POS
            OBD.cmd_LTFT = obd.commands.LONG_FUEL_TRIM_1
            OBD.cmd_STFT = obd.commands.SHORT_FUEL_TRIM_1
            OBD.cmd_TimingAdv = obd.commands.TIMING_ADVANCE
            OBD.cmd_MAF = obd.commands.MAF
            OBD.cmd_RunTime = obd.commands.RUN_TIME
            OBD.cmd_FuelLevel = obd.commands.FUEL_LEVEL
            OBD.cmd_WarmUpsSinceDTC = obd.commands.WARMUPS_SINCE_DTC_CLEAR
            OBD.cmd_DistanceSinceDTC = obd.commands.DISTANCE_SINCE_DTC_CLEAR
            OBD.cmd_CatTemp = obd.commands.CATALYST_TEMP_B1S1
            OBD.Connected = 1
            print ("OBD System is Ready")
        except:
            print ("Error setting OBD vars.")

    def OBD_update_thread(self):
        while OBD.Connected == 0:  # wait here while OBD system initializes
            pass
        while OBDPresent and OBD.Connected:
            if OBD.enable.Speed:
                try:
                    response_SPEED = OBD.connection.query(OBD.cmd_Speed)  # send the command, and parse the response
                    if str(response_SPEED.value.magnitude) != 'None':  # only proceed if string value is not None
                        try:
                            OBD.Speed = math.floor(int(response_SPEED.value.magnitude))  # Set int value
                            if sys.SpeedUnit == "MPH":  # change units if necessary
                                OBD.Speed = OBD.Speed * 0.6213711922
                            if OBD.Speed > OBD.Speed_max:  # set MAX variable if higher
                                OBD.Speed_max = OBD.Speed
                        except:
                            print("OBD Value Error - Speed")
                except:
                    print("Could not get OBD Response - Speed")


            if OBD.enable.RPM:
                try:
                    response_RPM = OBD.connection.query(OBD.cmd_RPM)
                    if str(response_RPM.value.magnitude) != 'None':
                        try:
                            OBD.RPM = math.floor(int(response_RPM.value.magnitude))
                            if OBD.RPM > OBD.RPM_max:
                                OBD.RPM_max = OBD.RPM
                        except:
                            print("OBD Value Error - RPM")
                except:
                    print("Could not get OBD Response - RPM")

            if OBD.enable.CoolantTemp:
                try:
                    response_CoolantTemp = OBD.connection.query(OBD.cmd_CoolantTemp)
                    if str(response_CoolantTemp.value.magnitude) != 'None':
                        try:
                            OBD.CoolantTemp = math.floor(int(response_CoolantTemp.value.magnitude))
                            if sys.TempUnit == "F":
                                OBD.CoolantTemp = OBD.CoolantTemp * 9.0 / 5.0 + 32.0
                            if OBD.CoolantTemp < 140:  # used to make screen look better (reduce size of Coolant bar)
                                OBD.CoolantTemp_ForBar = 0
                            else:
                                OBD.CoolantTemp_ForBar = OBD.CoolantTemp - 140
                        except:
                            print("OBD Value Error - Coolant Temp")
                except:
                    print("Could not get OBD Response - Coolant Temp")

            if OBD.enable.IntakeTemp:
                try:
                    response_IntakeTemp = OBD.connection.query(OBD.cmd_IntakeTemp)
                    if str(response_IntakeTemp.value.magnitude) != 'None':
                        try:
                            OBD.IntakeTemp = math.floor(int(response_IntakeTemp.value.magnitude))
                            if sys.TempUnit == "F":
                                OBD.IntakeTemp = OBD.IntakeTemp * 9.0 / 5.0 + 32.0
                        except:
                            print("OBD Value Error - Intake Temp")
                except:
                    print("Could not get OBD Response - Intake Temp")

            if OBD.enable.IntakePressure:
                try:
                    response_IntakePressure = OBD.connection.query(OBD.cmd_IntakePressure)
                    if str(response_IntakePressure.value.magnitude) != 'None':
                        try:
                            OBD.IntakePressure = math.floor(int(response_IntakePressure.value.magnitude))  # kPa
                        except:
                            print("OBD Value Error - Intake Press")
                except:
                    print("Could not get OBD Response - Intake Pressure")

            if OBD.enable.ThrottlePos:
                try:
                    response_ThrottlePos = OBD.connection.query(OBD.cmd_ThrottlePos)
                    if str(response_ThrottlePos.value.magnitude) != 'None':
                        try:
                            OBD.ThrottlePos = math.floor(int(response_ThrottlePos.value.magnitude))
                        except:
                            print("OBD Value Error - Throttle Position")
                except:
                    print("Could not get OBD Response - Throttle Position")

            if OBD.enable.Load:
                try:
                    response_Load = OBD.connection.query(OBD.cmd_Load)
                    if str(response_Load.value.magnitude) != 'None':
                        try:
                            OBD.Load = math.floor(int(response_Load.value.magnitude))
                        except:
                            print("OBD Value Error - Load")
                except:
                    print("Could not get OBD Response - Load")

            if OBD.enable.LTFT:
                try:
                    response_LTFT = OBD.connection.query(OBD.cmd_LTFT)
                    if str(response_LTFT.value.magnitude) != 'None':
                        try:
                            OBD.LTFT = math.floor(int(response_LTFT.value.magnitude))
                        except:
                            print("OBD Value Error - LTFT")
                except:
                    print("Could not get OBD Response - LTFT")

            if OBD.enable.STFT:
                try:
                    response_STFT = OBD.connection.query(OBD.cmd_STFT)
                    if str(response_STFT.value.magnitude) != 'None':
                        try:
                            OBD.STFT = math.floor(int(response_STFT.value.magnitude))
                        except:
                            print("OBD Value Error - STFT")
                except:
                    print("Could not get OBD Response - STFT")

            if OBD.enable.TimingAdv:
                try:
                    response_TimingAdv = OBD.connection.query(OBD.cmd_TimingAdv)
                    if str(response_TimingAdv.value.magnitude) != 'None':
                        try:
                            OBD.TimingAdv = math.floor(int(response_TimingAdv.value.magnitude))
                        except:
                            print("OBD Value Error - Timing Advance")
                except:
                    print("Could not get OBD Response - Timing Advance")

            if OBD.enable.MAF:
                try:
                    response_MAF = OBD.connection.query(OBD.cmd_MAF)
                    if str(response_MAF.value.magnitude) != 'None':
                        try:
                            OBD.MAF = math.floor(int(response_MAF.value.magnitude))  # grams/sec
                        except:
                            print("OBD Value Error - MAF")
                except:
                    print("Could not get OBD Response - MAF")

            if OBD.enable.RunTime:
                try:
                    response_RunTime = OBD.connection.query(OBD.cmd_RunTime)
                    if str(response_RunTime.value.magnitude) != 'None':
                        try:
                            OBD.RunTime = math.floor(int(response_RunTime.value.magnitude))  # Minutes
                        except:
                            print("OBD Value Error - RunTime")
                except:
                    print("Could not get OBD Response - RunTime")

            if OBD.enable.FuelLevel:
                try:
                    response_FuelLevel = OBD.connection.query(OBD.cmd_FuelLevel)
                    if str(response_FuelLevel.value.magnitude) != 'None':
                        try:
                            OBD.FuelLevel = math.floor(int(response_FuelLevel.value.magnitude))
                        except:
                            print("OBD Value Error - Fuel Level")
                except:
                    print("Could not get OBD Response - Fuel Level")

            if OBD.enable.WarmUpsSinceDTC:
                try:
                    response_WarmUpsSinceDTC = OBD.connection.query(OBD.cmd_WarmUpsSinceDTC)
                    if str(response_WarmUpsSinceDTC.value.magnitude) != 'None':
                        try:
                            OBD.WarmUpsSinceDTC = math.floor(int(response_WarmUpsSinceDTC.value.magnitude))
                        except:
                            print("OBD Value Error - Warm Ups Since DTC")
                except:
                    print("Could not get OBD Response - Warm Ups Since DTC")

            if OBD.enable.DistanceSinceDTC:
                try:
                    response_DistanceSinceDTC = OBD.connection.query(OBD.cmd_DistanceSinceDTC)
                    if str(response_DistanceSinceDTC.value.magnitude) != 'None':
                        try:
                            OBD.DistanceSinceDTC = math.floor(int(response_DistanceSinceDTC.value.magnitude))
                            if sys.SpeedUnit == "MPH":
                                OBD.DistanceSinceDTC = OBD.DistanceSinceDTC * 0.6213711922
                        except:
                            print("OBD Value Error - Distance Since DTC")
                except:
                    print("Could not get OBD Response - Distance Since DTC")

            if OBD.enable.CatTemp:
                try:
                    response_CatTemp = OBD.connection.query(OBD.cmd_CatTemp)
                    if str(response_CatTemp.value.magnitude) != 'None':
                        try:
                            OBD.CatTemp = math.floor(int(response_CatTemp.value.magnitude))
                            if sys.TempUnit == "F":
                                OBD.CatTemp = OBD.CatTemp * 9.0 / 5.0 + 32.0
                        except:
                            print("OBD Value Error - Cat Temp")
                except:
                    print("Could not get OBD Response - Cat Temp")

    def start_threads(self):
        OBDSetupThread = threading.Thread(name='obd_setup_thread', target=self.OBD_setup_thread)
        OBDUpdateThread = threading.Thread(name='obd_update_thread', target=self.OBD_update_thread)
        OBDSetupThread.start()
        OBDUpdateThread.start()

if OBDPresent == 1:
    OBD().start_threads()

class RGB:
    Enable = RGBEnabled  # from global config variable
    Mode = "default"
    DC_R_DR = 0
    DC_G_DR = 0
    DC_B_DR = 0
    DC_R_AS = 0
    DC_G_AS = 0
    DC_B_AS = 0

    if Enable == 1:
        try:
            GPIO.setup(20, GPIO.OUT)  # assign as output
            GPIO.setup(21, GPIO.OUT)
            GPIO.setup(16, GPIO.OUT)
            GPIO.setup(13, GPIO.OUT)
            GPIO.setup(19, GPIO.OUT)
            GPIO.setup(26, GPIO.OUT)

            LED_R_DR = GPIO.PWM(20, 100)  # Initialize PWM @ 100Hz frequency
            LED_G_DR = GPIO.PWM(21, 100)
            LED_B_DR = GPIO.PWM(16, 100)
            LED_R_AS = GPIO.PWM(13, 100)
            LED_G_AS = GPIO.PWM(19, 100)
            LED_B_AS = GPIO.PWM(26, 100)

            LED_R_DR.start(DC_R_DR)  # turn on and use 0 DC as default
            LED_G_DR.start(DC_G_DR)
            LED_B_DR.start(DC_B_DR)
            LED_R_AS.start(DC_R_AS)
            LED_G_AS.start(DC_G_AS)
            LED_B_AS.start(DC_B_AS)
        except:
            print ("Could not set up RGB System")

class var:
    Redline = 7500
    SpeedLimit = 75

# ---------------------------------------------------------------------------------------------------------------------------------------------
# A few initial functions to run for setup
sys().loaddata()

if developermode == 0:
    if autobrightness == 1:
        currenthour = int(time.strftime("%-H"))  # hour as decimal (24hour)
        if currenthour < 7 or currenthour >= 20:  # earlier than 7am and later than 6pm -> dim screen on start
            sys().setbrightness(15)
        else:
            sys().setbrightness(255)

    if autobrightness == 2:  # start on dim every time
        sys().setbrightness(15)

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Define Kivy Classes
#MAIN SCREEN CLASSES
class MultiGaugeScreen(Screen):
    pass
class PerformanceScreen(Screen):
    pass
class CarInfoScreen(Screen):
    pass
class CoolantScreen(Screen):
    pass
class RPMScreen(Screen):
    pass
class MenuScreen(Screen):
    pass
class RGBScreen(Screen):
    pass

#ROOT CLASSES
class ROOT(FloatLayout):
    sm = ObjectProperty()

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Main App Class
class MainApp(App):
    def build(self):
        root = ROOT()
        KVFILE = Builder.load_file("main.kv")
        root.add_widget(KVFILE)  # adds the main GUI

        Clock.schedule_interval(self.updatevariables, .1)
        Clock.schedule_interval(self.updateOBDdata, .01)

        return root

# ---------------------------------------------------------------------------------------------------------------------------------------------
    theme_cls = ThemeManager()
    version = StringProperty()
    ipAddress = StringProperty()
    WifiNetwork = StringProperty()
    CPUTemp = NumericProperty(0)
    CPUVolts = NumericProperty(0)
    shutdownflag = NumericProperty()
    theme_cls.theme_style = "Dark"
    theme_cls.primary_palette = "Red"

    Redline = NumericProperty(0)
    SpeedLimit = NumericProperty(0)

    Speed = NumericProperty(0)
    Speed_max = NumericProperty(0)
    RPM = NumericProperty(0)
    RPM_max = NumericProperty(0)
    CoolantTemp = NumericProperty(0)
    CoolantTemp_ForBar = NumericProperty(0)
    IntakeTemp = NumericProperty(0)
    IntakePressure = NumericProperty(0)
    Load = NumericProperty(0)
    ThrottlePos = NumericProperty(0)
    FuelLevel = NumericProperty(0)
    LTFT = NumericProperty(0)
    STFT = NumericProperty(0)
    TimingAdv = NumericProperty(0)
    MAF = NumericProperty(0)
    RunTime = NumericProperty(0)
    WarmUpsSinceDTC = NumericProperty(0)
    DistanceSinceDTC = NumericProperty(0)
    CatTemp = NumericProperty(0)

    RPMWarn = NumericProperty(0)
    SpeedWarn = NumericProperty(0)
    CoolantTempWarn = NumericProperty(0)
    IntakeTempWarn = NumericProperty(0)
    LTFTWarn = NumericProperty(0)
    STFTWarn = NumericProperty(0)
    CatTempWarn = NumericProperty(0)

    RGBSlider_R_DR_value = NumericProperty(0)
    RGBSlider_G_DR_value = NumericProperty(0)
    RGBSlider_B_DR_value = NumericProperty(0)
    RGBSlider_R_AS_value = NumericProperty(0)
    RGBSlider_G_AS_value = NumericProperty(0)
    RGBSlider_B_AS_value = NumericProperty(0)

    def updatevariables(self, *args):
        self.version = sys.version
        self.shutdownflag = sys.shutdownflag
        self.RPMWarn = OBD.warning.RPM
        self.SpeedWarn = OBD.warning.Speed
        self.CoolantTempWarn = OBD.warning.CoolantTemp
        self.IntakeTempWarn = OBD.warning.IntakeTemp
        self.LTFTWarn = OBD.warning.LTFT
        self.STFTWarn = OBD.warning.STFT
        self.CatTempWarn = OBD.warning.CatTemp
        self.ipAddress = sys.ip
        self.WifiNetwork = sys.ssid
        self.CPUVolts = sys.CPUVolts
        self.CPUTemp = sys.CPUTemp
        if sys.getsysteminfo == True:
            self.get_CPU_info()
            self.get_IP()
        self.RGBSlider_R_DR_value = RGB.DC_R_DR
        self.RGBSlider_G_DR_value = RGB.DC_G_DR
        self.RGBSlider_B_DR_value = RGB.DC_B_DR
        self.RGBSlider_R_AS_value = RGB.DC_R_AS
        self.RGBSlider_G_AS_value = RGB.DC_G_AS
        self.RGBSlider_B_AS_value = RGB.DC_B_AS

    def updateOBDdata(self, *args):
        if OBD.Connected and developermode == 0:
            try:
                self.Speed = OBD.Speed
                self.Speed_max = OBD.Speed_max
                self.RPM = OBD.RPM
                self.RPM_max = OBD.RPM_max
                self.CoolantTemp = OBD.CoolantTemp
                self.CoolantTemp_ForBar = OBD.CoolantTemp_ForBar
                self.IntakeTemp = OBD.IntakeTemp
                self.IntakePressure = OBD.IntakePressure
                self.Load = OBD.Load
                self.ThrottlePos = OBD.ThrottlePos
                self.LTFT = OBD.LTFT
                self.STFT = OBD.STFT
                self.TimingAdv = OBD.TimingAdv
                self.MAF = OBD.MAF
                self.RunTime = OBD.RunTime
                self.FuelLevel = OBD.FuelLevel
                self.WarmUpsSinceDTC = OBD.WarmUpsSinceDTC
                self.DistanceSinceDTC = OBD.DistanceSinceDTC
                self.CatTemp = OBD.CatTemp
            except:
                print ("Python -> Kivy OBD Var Setting Failure")

        if OBD.Connected == 0 and developermode:
            #Speedo Dev Code
            if OBD.dev.Speed_inc == 1:
                OBD.dev.Speed = OBD.dev.Speed + 1
            else:
                OBD.dev.Speed = OBD.dev.Speed - 1
            if OBD.dev.Speed > 125:
                OBD.dev.Speed_inc = 0
            if OBD.dev.Speed < 1:
                OBD.dev.Speed_inc = 1
            if OBD.dev.Speed > OBD.dev.Speed_max:
                OBD.dev.Speed_max = OBD.dev.Speed

            self.Speed = OBD.dev.Speed
            self.SpeedLimit = var.SpeedLimit

            #Tach Dev Code
            if OBD.dev.RPM_inc == 1:
                OBD.dev.RPM = OBD.dev.RPM + 10
            else:
                OBD.dev.RPM = OBD.dev.RPM - 10
            if OBD.dev.RPM > 7700:
                OBD.dev.RPM_inc = 0
            if OBD.dev.RPM < 100:
                OBD.dev.RPM_inc = 1
            if OBD.dev.RPM > OBD.dev.RPM_max:
                OBD.dev.RPM_max = OBD.dev.RPM
            self.RPM = OBD.dev.RPM
            self.RPM_max = OBD.dev.RPM_max
            self.Redline = var.Redline

            #Coolant Dev Code
            if OBD.dev.CoolantTemp_inc == 1:
                OBD.dev.CoolantTemp = OBD.dev.CoolantTemp + 1
            else:
                OBD.dev.CoolantTemp = OBD.dev.CoolantTemp - 1
            if OBD.dev.CoolantTemp > 219:
                OBD.dev.CoolantTemp_inc = 0
            if OBD.dev.CoolantTemp < 1:
                OBD.dev.CoolantTemp_inc = 1
            if OBD.dev.CoolantTemp < 140:  # used to make screen look better (reduce size of Coolant bar)
                OBD.dev.CoolantTemp_ForBar = 0
            else:
                OBD.dev.CoolantTemp_ForBar = OBD.dev.CoolantTemp - 140
            self.CoolantTemp = OBD.dev.CoolantTemp
            self.CoolantTemp_ForBar = OBD.dev.CoolantTemp_ForBar

            # FuelTrim Dev Code
            if OBD.dev.FuelTrim_inc == 1:
                OBD.dev.FuelTrim = OBD.dev.FuelTrim + 1
            else:
                OBD.dev.FuelTrim = OBD.dev.FuelTrim - 1
            if OBD.dev.FuelTrim > 24:
                OBD.dev.FuelTrim_inc = 0
            if OBD.dev.FuelTrim < -24:
                OBD.dev.FuelTrim_inc = 1
            self.LTFT = OBD.dev.FuelTrim
            self.STFT = OBD.dev.FuelTrim
            self.TimingAdv = OBD.dev.FuelTrim

            #Generic Dev Code
            if OBD.dev.Generic_inc == 1:
                OBD.dev.Generic = OBD.dev.Generic + 1
            else:
                OBD.dev.Generic = OBD.dev.Generic - 1
            if OBD.dev.Generic > 99:
                OBD.dev.Generic_inc = 0
            if OBD.dev.Generic < 10:
                OBD.dev.Generic_inc = 1
            self.IntakeTemp = OBD.dev.Generic
            self.ThrottlePos = OBD.dev.Generic
            self.MAF = OBD.dev.Generic
            self.RunTime = OBD.dev.Generic
            self.FuelLevel = OBD.dev.Generic
            self.WarmUpsSinceDTC = OBD.dev.Generic
            self.DistanceSinceDTC = OBD.dev.Generic
            self.CatTemp = OBD.dev.Generic

# ---------------------------------------------------------------------------------------------------------------------------------------------
# Scheduling Functions
    def save(obj):
        sys().savedata() # save new varibles for next boot

    def shutdown(obj):
        os.system("sudo shutdown -h now")

    def reboot(obj):
        os.system("sudo reboot")

    def killapp(obj):
        os.system("sudo killall python") # Kills all running processes and threads

    def ScreenOnOff(obj,action):
        if action == "ON":
            sys.screen = 1
            os.system("sudo echo 0 > /sys/class/backlight/rpi_backlight/bl_power")  # turns screen on
        elif action == "OFF":
            sys.screen = 0
            os.system("sudo echo 1 > /sys/class/backlight/rpi_backlight/bl_power")  # turns screen off

    #brightness control function
    def BrightnessSet(obj,brightvalue):
        brightnesscommand = "sudo echo "+str(brightvalue)+" > /sys/class/backlight/rpi_backlight/brightness"
        os.system(brightnesscommand)
        sys.brightness = brightvalue

    def get_IP(obj):
        if developermode == 0:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                sys.ip = s.getsockname()[0]
            except:
                sys.ip = "No IP address found..."
                print ("Could not get IP")
            try:
                ssidstr = str(subprocess.check_output("iwgetid -r", shell=True))
                sys.ssid = ssidstr[2:-3]
            except:
                sys.ssid = "No SSID found..."
                print ("Could not get SSID")

    def get_CPU_info(obj):
        if developermode == 0:
            try:
                tFile = open('/sys/class/thermal/thermal_zone0/temp')
                temp = float(tFile.read())
                tempC = temp / 1000
                tempF = tempC * 9.0 / 5.0 + 32.0
                sys.CPUTemp = round(tempC,2)
            except:
                print ("Could not get CPU Temp")
                sys.CPUTemp = 0
            try:
                voltstr = str(subprocess.check_output(["/opt/vc/bin/vcgencmd", "measure_volts core"]))
                sys.CPUVolts = float(voltstr.split('=')[1][:-4])
            except:
                print ("Could not get CPU core Voltage")
                sys.CPUVolts = 0

    def zero_out_max(obj):
        OBD.RPM_max = 0
        OBD.Speed_max = 0
        OBD.dev.RPM_max = 0
        OBD.dev.Speed_max = 0

    def OBDEnabler(obj, PID, status):
        setattr(OBD.enable, PID, status)  # sets OBD enable class based on PID (text) and Status (int) input

    def OBDOFF(obj):
        OBD.enable.RPM = 0
        OBD.enable.Speed = 0
        OBD.enable.CoolantTemp = 0
        OBD.enable.IntakeTemp = 0
        OBD.enable.IntakePressure = 0
        OBD.enable.Load = 0
        OBD.enable.ThrottlePos = 0
        OBD.enable.LTFT = 0
        OBD.enable.STFT = 0
        OBD.enable.TimingAdv = 0
        OBD.enable.MAF = 0
        OBD.enable.RunTime = 0
        OBD.enable.FuelLevel = 0
        OBD.enable.WarmUpsSinceDTC = 0
        OBD.enable.DistanceSinceDTC = 0
        OBD.enable.CatTemp = 0

    def CoolantTempWarnSlider(self, instance, value):
        OBD.warning.CoolantTemp = int(math.floor(value))
    def IntakeTempWarnSlider(self, instance, value):
        OBD.warning.IntakeTemp = int(math.floor(value))
    def CatTempWarnSlider(self, instance, value):
        OBD.warning.CatTemp = int(math.floor(value))
    def STFTWarnSlider(self, instance, value):
        OBD.warning.STFT = int(math.floor(value))
    def LTFTWarnSlider(self, instance, value):
        OBD.warning.LTFT = int(math.floor(value))
    def RPMWarnSlider(self, instance, value):
        OBD.warning.RPM = int(math.floor(value))
    def SpeedWarnSlider(self, instance, value):
        OBD.warning.Speed = int(math.floor(value))

    def RGBSlider_Color_Side(obj, value, color, side): #was self, not obj..........
        if side == "DR":
            if color == "R":
                RGB.DC_R_DR = int(math.floor(value))
            if color == "G":
                RGB.DC_G_DR = int(math.floor(value))
            if color == "B":
                RGB.DC_B_DR = int(math.floor(value))
        if side == "AS":
            if color == "R":
                RGB.DC_R_AS = int(math.floor(value))
            if color == "G":
                RGB.DC_G_AS = int(math.floor(value))
            if color == "B":
                RGB.DC_B_AS = int(math.floor(value))

    def Set_RGB_Mode(obj, mode):
        RGB.Mode = mode

    def Set_RGB_All(obj, R_DR, G_DR, B_DR, R_AS, G_AS, B_AS):
        RGB.DC_R_DR = R_DR
        RGB.DC_G_DR = G_DR
        RGB.DC_B_DR = B_DR
        RGB.DC_R_AS = R_AS
        RGB.DC_G_AS = G_AS
        RGB.DC_B_AS = B_AS

# ---------------------------------------------------------------------------------------------------------------------------------------------
if __name__ =='__main__':
    MainApp().run()