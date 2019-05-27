# Usage: 
#   Run with python3:
#     python3 ~pi/projects/oled/display.py "line 1" "line 2" "line 3" "line 4"
#   or in a bash script:
#     python3 ~pi/projects/oled/display.py "$@"
#   then
#     ./my_script.sh "line 1" "line 2" "line 3" "line 4"

import sys
from board import SCL, SDA
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont

class Display:
    'Class for writing to an onboard OLED display'

    def __init__(self):
        i2c = busio.I2C(SCL, SDA)
        self.screen = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
        self.font = ImageFont.truetype('/PATH/TO/FONT/slkscr.ttf', 8)

    def clear(self):
        "Clear display"
        self.screen.fill(0)
        self.screen.show()

    def draw_lines(self, line1, line2, line3, line4):
        image = Image.new('1', (self.screen.width, self.screen.height))
        draw = ImageDraw.Draw(image)
        left = 0
        top = -2
        bottom = self.screen.height + 2
        draw.text((left, top),    line1, font=self.font, fill=255)
        draw.text((left, top+8),  line2, font=self.font, fill=255)
        draw.text((left, top+16), line3, font=self.font, fill=255)
        draw.text((left, top+24), line4, font=self.font, fill=255)
        self.screen.image(image)
        self.screen.show()

display = Display()
display.clear()
args = (sys.argv[1:] + 4 * [""])[:4]
display.draw_lines(args[0], args[1], args[2], args[3])

