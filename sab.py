# Import Python System Libraries
import time
import json
import random
import signal
import sys
import os
 
# Import Requests Library
import requests
 
# Import Blinka
from board import SCL, SDA
import busio
import adafruit_ssd1306
 
# Import Python Imaging Library
from PIL import Image, ImageDraw, ImageFont

class SabQueue:
    'Class to represent a queue in SABnzbd'

    def __init__(self, queue_data):
        self.queue_data = queue_data
        self.items = queue_data['slots']
        self.status = queue_data['status']
        self.time_left = queue_data['timeleft']

    def is_downloading(self):
        return self.status == 'Downloading'

class PlexActivity:
    'Class to represent activity in Plex'
    def __init__(self, activity_data):
        self.sessions = activity_data['sessions']
        self.stream_count = activity_data['stream_count']

    def active_streams(self):
        return len([session for session in self.sessions if session['state'] == 'playing'])

    def titles(self):
        return [session['title'] for session in self.sessions]

    def summary(self):
        return [(s['friendly_name'], s['title'], s['state']) for s in self.sessions]

class PlexAPI:
    'Class for accessing the Tautulli API'

    def __init__(self, base_url, api_key):
        self.base_url = base_url + '/api/v2?apikey=' + api_key

    def get_activity(self):
        url = self.__build_url("cmd=get_activity")
        print(url)
        response = requests.get(url).json()
        data = response['response']['data']
        return PlexActivity(data)

    def __build_url(self, action):
        "takes an api action like `'cmd=get_activity'` and returns the full url"
        return self.base_url + '&' + action

class SabAPI:
    'Class for accessing the SABnzbd API'

    def __init__(self, base_url, api_key):
        self.base_url = base_url + '/api?output=json&apikey=' + api_key
    
    def pause_queue(self):
        url = self.__build_url("mode=pause")
        requests.get(url)

    def resume_queue(self):
        url = self.__build_url("mode=resume")
        requests.get(url)

    def get_queue(self):
        url = self.__build_url("mode=queue")
        response = requests.get(url)
        data = response.json()
        return SabQueue(data['queue'])
    
    def __build_url(self, action):
        "takes an api action like `'mode=queue'` and returns the full url"
        return self.base_url + '&' + action

class SabStatus:
    'Class for checking the status of SABnzbd and updating an onboard OLED display'

    def __init__(self, sab_api, plex_api):
        self.sab_api = sab_api
        self.plex_api = plex_api
        self.disp = self.__init_disp()

    def __init_disp(self):
        # Create the I2C interface.
        i2c = busio.I2C(SCL, SDA)
         
        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.
        return adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
         
    def clear_screen(self):
        "Clear display"
        self.disp.fill(0)
        self.disp.show()

    def draw(self):
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        width = self.disp.width
        height = self.disp.height
        image = Image.new('1', (width, height))
         
        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)
         
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
         
        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = -2
        top = padding
        bottom = height - padding
        # Move left to right keeping track of the current x position
        # for drawing shapes.
        x = 0
         
        # Load nice silkscreen font
        font = ImageFont.truetype('/PATH/TO/FONT/slkscr.ttf', 8)
 
        while True:
            new_x = x + random.randint(0,4)
            new_top = top + random.randint(0,4)

            # Draw a black filled box to clear the image.
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
         
            try:
                queue = self.sab_api.get_queue()
                activity = plex_api.get_activity()

                if str(activity.stream_count) == "0":
                    plex_activity_line = "No streams"
                elif str(activity.stream_count) == "1":
                    (name, title, status) = activity.summary()[0]
                    plex_activity_line = name + " " + status + " " + title
                else:
                    names = [name for (name, _title, _state) in activity.summary()]
                    plex_activity_line = ", ".join(names) + " streaming now"

                sab_items = len(queue.items)
                if sab_items == 0:
                    sab_status_line = "SAB " + queue.status + " no queue"
                elif sab_items == 1:
                    sab_status_line = "SAB " + queue.status + " " + str(sab_items) + " item"
                else:
                    sab_status_line = "SAB " + queue.status + " " + str(sab_items) + " items"

                if queue.is_downloading():
                    time_left = queue.time_left + " remaining"
                else:
                    time_left = ""
                draw.text((new_x, new_top), sab_status_line, font=font, fill=255)
                draw.text((new_x, new_top+7), time_left, font=font, fill=255)
                draw.text((new_x, new_top+16), plex_activity_line, font=font, fill=255)
                draw.text((new_x, new_top+24), "",  font=font, fill=255)
            except Exception as error:
                print("Cannot Draw")
                draw.text((new_x, new_top), "Error", font=font, fill=255)
                time.sleep(1)
            
            # Display image.
            self.disp.image(image)
            self.disp.show()
            time.sleep(1)

try:
    SAB_ADDRESS = os.environ['SAB_ADDRESS']
    SAB_API_KEY = os.environ['SAB_API_KEY']
    TAUTULLI_ADDRESS = os.environ['TAUTULLI_ADDRESS']
    TAUTULLI_API_KEY = os.environ['TAUTULLI_API_KEY']
except KeyError: 
    print('Please configure your environment with SAB_ADDRESS, SAB_API_KEY, TAUTULLI_ADDRESS, and TAUTULLI_API_KEY')
else:
    sab_api = SabAPI(SAB_ADDRESS, SAB_API_KEY)
    plex_api = PlexAPI(TAUTULLI_ADDRESS, TAUTULLI_API_KEY)
    sab_status = SabStatus(sab_api, plex_api)

    def signal_handler(sig, frame):
        sab_status.clear_screen()
        print()
        print('Byeee')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print('SABnzbd Status Checker starting')
    print('Press Ctrl+C to exit')
    sab_status.draw()
