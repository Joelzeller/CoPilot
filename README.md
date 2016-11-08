# CoPilot
Raspberry Pi powered in-car infotainment system

Check out my website for more info: http://joelzeller.wixsite.com/copilot

**Setup:**
-	Get Kivy: https://kivy.org/docs/installation/installation-rpi.html
-	Get Kivy Garden: https://kivy.org/docs/api-kivy.garden.html 
		 	 https://kivy-garden.github.io/
-	Get KivyMD: https://gitlab.com/kivymd/KivyMD
-	Get python-OBD: https://github.com/brendan-w/python-OBD

-	This should install garden and then recycleview, and that should be enough to get it working
	
	pip install kivy-garden
	
	garden install recycleview

-	Python Version 2.7.0 is recommended

**You will need clock.kv, main.kv, main.py, and the data folder placed in a directory on your pi - mine are located at /home/pi/CoPilot**

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
- This turns off things like GPIO, temp probe, and OBD stuff as it doesn’t place nice on a computer other than the Pi.
-  Change the “developermode” var to 1.  Change this to 0 if you’d like to use all of CoPilot’s features.

**To view current temp:**
- Make sure "TempProbePresent" variable in code is set to 1 - if not, temp will be "--"
- Tap under time on home screen and bubble will float unto screen showing temp - tap again to hide
 
**Email me at joelzeller25@hotmail.com with any questions :)
