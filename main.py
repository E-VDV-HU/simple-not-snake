"""
Connections: MAX7219 LED Matrix to Raspberry Pi Pico W
 * VCC -> VBUS (5V, physical pin 40)
 * GND -> GND (physical pin 3)
 * DIN -> GPIO3 (physical pin 5)
 * CS  -> GPIO5 (physical pin 7)
 * CLK -> GPIO2 (physical pin 4)

Connections: Analog Keypad 1
 * VCC    -> 3V3 OUT (physical pin 36)
 * GND    -> GND
 * Signal -> GP26 (ADC0, physical pin 31)

Connections: Score LEDs
 * LED 1 -> GPIO6  (physical pin 9)
 * LED 2 -> GPIO7  (physical pin 10)
 * LED 3 -> GPIO8  (physical pin 11)
 * LED 4 -> GPIO9  (physical pin 12)
 * LED 5 -> GPIO10 (physical pin 14)
"""

#import
from machine import Pin, SPI, ADC # pyright: ignore[reportMissingImports, reportMissingModuleSource]
import utime # pyright: ignore[reportMissingImports, reportMissingModuleSource]
import random

try:
    import max7219
except:
    raise ImportError("Library max7219 is not installed.")

#vars
brightness = 10 #between 0 and 15
keypad_pin1 = 26
score_led_pins = [6,7,8,9,10]

#snake
player = [4,4] # default position
food = None
score = 0
game_over = False

#vars check
if brightness < 0 or brightness > 15:
    raise ValueError("Brightness must be between 0 and 15")

#autoconfig
spi = SPI(0, baudrate=10_000_000, polarity=1, phase=0, sck=Pin(2), mosi=Pin(3))
ss = Pin(5, Pin.OUT)
keypad_1 = ADC(Pin(keypad_pin1))

display = max7219.Matrix8x8(spi, ss, 1)
display.brightness(brightness)
display.set_rotation(270) # default max7219 driver, not changed by claude.

#score leds
score_leds = []

for pin in score_led_pins:
    score_leds.append(Pin(pin, Pin.OUT))

for led in score_leds:
    led.on()

# Clear the display @ boot.
display.fill(0)
display.show()

#keypad
def read_keypad(keypad): #ripped from gameconsole project
    value = keypad.read_u16()
    if 8700 <= value <= 10022:
        return "UP"
    elif 20800 <= value <= 21952:
        return "DOWN"
    elif 0 <= value <= 880:
        return "LEFT"
    elif 32000 <= value <= 33147:
        return "RIGHT"
    elif 47190 <= value <= 48300:
        return "ACTION"
    return None

#snake
def move_player(key):
    x = player[0]
    y = player[1]

    if key == "UP":
        y -= 1
    elif key == "DOWN":
        y += 1
    elif key == "LEFT":
        x -= 1
    elif key == "RIGHT":
        x += 1

    #check walls
    if x >= 0 and x <= 7 and y >= 0 and y <= 7:
        player[0] = x
        player[1] = y

def spawn_food():
    while True:
        food = [random.randint(0,7), random.randint(0,7)]

        if food != player:
            return food

def draw_snake():
    display.pixel(player[0], player[1], 1)
    if (utime.ticks_ms() // 300) % 2 == 0:
        display.pixel(food[0], food[1], 1)


def finish_game():
    display.fill(0)

    #game over
    display.fill(0)
    matrix_LIST = [
        [1, 1, 0, 0, 0, 0, 1, 1],
        [1, 1, 1, 0, 0, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 0, 0, 1, 1, 1],
        [1, 1, 0, 0, 0, 0, 1, 1]
    ]
    display.write_matrix(matrix_LIST)
    display.show()
    utime.sleep(2)

def snake():
    global food, score, game_over

    food = spawn_food()

    while True:
        display.fill(0)
        draw_snake()
        display.show()
        utime.sleep(0.1)

        key = read_keypad(keypad_1)

        if key in ("UP", "DOWN", "LEFT", "RIGHT"):
            while (read_keypad(keypad_1) == key):
                utime.sleep(0.02)

            move_player(key)

            #check food
            if player == food:
                score += 1

                #update score leds
                score_leds[score - 1].off()

                if score == 5:
                    game_over = True
                else:
                    food = spawn_food()

        if game_over:
            break

    finish_game()

if __name__ == "__main__":
    snake()