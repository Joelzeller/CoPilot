# CoPilot
Raspberry Pi powered in-car infotainment system

Check out my website for more info: http://joelzeller.wixsite.com/copilot

**Setup:**
-	Get Kivy: https://kivy.org/docs/installation/installation-rpi.html
-	Get Kivy Garden: https://kivy.org/docs/api-kivy.garden.html 
		 	 https://kivy-garden.github.io/
-	Get KivyMD: https://gitlab.com/kivymd/KivyMD
-       Get Mapview: https://github.com/kivy-garden/garden.mapview
-	Get python-OBD: https://github.com/brendan-w/python-OBD

-	This should install garden and then recycleview, and that should be enough to get it working
	
	pip install kivy-garden
	
	garden install recycleview

-	Python Version 2.7.0 is recommended

**New setup required!**
For mapview to work, one program of kivy must be changed to handle an error.
-	sudo nano /usr/local/lib/python2.7/dist-packages/kivy/core/image/img_pygame.py
-	scroll down to find "image loader work only with rgb/rgba image"
-	delete the except statement that starts with Logger.warning('Image: Unable to convert.......') and ends with "raise"

**You will need main.kv, main.py, and the data folder placed in a directory on your pi - mine are located at /home/pi/CoPilot**

-	Setup to autorun on boot like I do or just run main.py

**Recommended Hardware:**

- Raspberry Pi 2 or 3 – increase the GPU memory to its max setting using raspi-config 
- Official Raspberry Pi 7 inch touchscreen
- Set up a RTC to keep time since Pi won’t be connected to the internet at all times
- Temperature Probe – place probe wherever desired, mine is inside the car
- Bluetooth OBDII dongle for car (for use with performance pages)
- Leds (Look in code for which GPIO is used)
- If you want to interface with an old radio, hook up relays to the old buttons and connect to the appropriate GPIO pins
- Two push buttons for Hotkeys (Look in code for which GPIO is used)


**How to use:**
 
To use developer mode:
- Changing the “developermode” var to 1 turns off things like GPIO, temp probe, and OBD stuff as it doesn’t place nice on a computer other than the Pi.
-  Change this var to 0 if you’d like to use all of CoPilot’s features.

**To view current temp:**
- Make sure "TempProbePresent" variable in code is set to 1 - if not, temp will be "--"
- Tap under time on home screen and bubble will float unto screen showing temp - tap again to hide

**To use bluetooth audio:**
- Chnage the MAC address in the code to the MAC address of your device
- Pair your device with the raspberry pi
- It works best if you start audio first and then tap the bluetooth button on the audio screen
- Track data and a progress bar should appear and the play/pause and seek buttons should work
 
**Email me at joelzeller25@hotmail.com with any questions :)
