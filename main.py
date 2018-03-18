from digitalio import DigitalInOut, Direction
import board
import busio
import time
import math
import neopixel
import ustruct as struct
import adafruit_ssd1306

# setup neopixel pins
pixpin = board.D3
numpix = 16
strip = neopixel.NeoPixel(pixpin, numpix, brightness=0.1, auto_write=False)

# Setup the OLED
i2c = busio.I2C(board.SCL, board.SDA)
reset_pin = DigitalInOut(board.D4) # any pin!
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3d, reset=reset_pin)

oled.fill(0)
oled.show()

# cause it's cool
oled.fill
oled.text('================',0 ,0)
oled.text('LOADING PROGRAM', 0, 7)
oled.text('  created by:', 0, 17)
oled.text(' Maxwell Staley', 0, 27)
oled.text('=================', 0, 50)
oled.show()
time.sleep(1.0)

# draw the screen

# i = 0
# while i in range(126):
#     oled.text('.', i, 40)
#     i = i + 1
#     oled.show()
#     time.sleep(.03)
# Connect the Sensor's TX pin to the board's RX pin
uart = busio.UART(board.TX, board.RX, baudrate=9600)
 
buffer = []

def led_show(aqi, numpix, max_value):
    ledcolors = [ [0, 255, 0],\
              [128, 239, 17],\
              [255, 225, 35],\
              [254, 165, 20],\
              [254, 117, 4],\
              [80, 174, 0],\
              [96, 158, 0],\
              [110, 142, 0],\
              [126, 126, 0],\
              [142, 100, 0],\
              [158,96,0],\
              [174,80,0],\
              [190,64,0],\
              [207,48,0],\
              [223,32,0],\
              [141,7,22], ]

    if aqi != 0:
        numShowPix = int((round(aqi / (max_value / numpix ))) + 1)
        if numShowPix > numpix:
            numShowPix = numpix
    else:
        numShowPix = 1 
    
    print(numShowPix)
    if numShowPix == 1:
        colors = ledcolors[0]
        red = colors[0]
        green = colors[1]
        blue = colors[2]
        strip[0] = (red, green, blue)
    else:
        for i in range(numShowPix):
            colors = ledcolors[i]
            red = colors[0]
            green = colors[1]
            blue = colors[2]
            strip[i] = (red, green, blue)

    # Fill the rest with 0
    for i in range(numShowPix, numpix):
        strip[i] = (0,0,0)
    # Update the strip
    strip.show()

def ugm3_to_aqi(ugm3):
    '''
    Convert concentration of PM2.5 particles in �g/ metre cubed to the USA 
    Environment Agency Air Quality Index - AQI
    https://en.wikipedia.org/wiki/Air_quality_index
    Computing_the_AQI
    https://github.com/intel-iot-devkit/upm/pull/409/commits/ad31559281bb5522511b26309a1ee73cd1fe208a?diff=split
    '''
    
    cbreakpointspm25 = [ [0.0, 12, 0, 50],\
                    [12.1, 35.4, 51, 100],\
                    [35.5, 55.4, 101, 150],\
                    [55.5, 150.4, 151, 200],\
                    [150.5, 250.4, 201, 300],\
                    [250.5, 350.4, 301, 400],\
                    [350.5, 500.4, 401, 500], ]
                    
    C=ugm3
    
    if C > 500.4:
        aqi=500

    else:
        for breakpoint in cbreakpointspm25:
            if breakpoint[0] <= C <= breakpoint[1]:
                Clow = breakpoint[0]
                Chigh = breakpoint[1]
                Ilow = breakpoint[2]
                Ihigh = breakpoint[3]
                aqi=(((Ihigh-Ilow)/(Chigh-Clow))*(C-Clow))+Ilow
    
    return aqi

peak = 0
while True:
    data = uart.read(32)  # read up to 32 bytes
    data = list(data)
    #print("read: ", data)          # this is a bytearray type
 
    buffer += data
    
    while buffer and buffer[0] != 0x42:
        buffer.pop(0)
    
    if len(buffer) < 32:
        continue
 
    if buffer[1] != 0x4d:
        buffer.pop(0)
        continue
 
    frame_len = struct.unpack(">H", bytes(buffer[2:4]))[0]
    if frame_len != 28:
        continue
 
    frame = struct.unpack(">HHHHHHHHHHHHHH", bytes(buffer[4:]))
 
    pm10_standard, pm25_standard, pm100_standard, pm10_env, pm25_env, pm100_env, particles_03um, particles_05um, particles_10um, particles_25um, particles_50um, particles_100um, skip, checksum = frame
 
    check = sum(buffer[0:30])
    
    if check != checksum:
        continue
    
    # convert SI units to US AQI
    # input should be 24 hour average of ugm3, not instantaneous reading
    aqi=ugm3_to_aqi(particles_25um)

    print("---------------------------------------")
    print("Current AQI (not 24 hour avg): ", str(int(aqi)))
    print("---------------------------------------")
    print("Concentration Units (standard)")
    print("---------------------------------------")
    print("PM 1.0: %d\tPM2.5: %d\tPM10: %d" % (pm10_standard, pm25_standard, pm100_standard))
    print("Concentration Units (environmental)")
    print("---------------------------------------")
    print("PM 1.0: %d\tPM2.5: %d\tPM10: %d" % (pm10_env, pm25_env, pm100_env))
    print("---------------------------------------")
    print("Particles > 0.3um / 0.1L air:", particles_03um)
    print("Particles > 0.5um / 0.1L air:", particles_05um)
    print("Particles > 1.0um / 0.1L air:", particles_10um)
    print("Particles > 2.5um / 0.1L air:", particles_25um)
    print("Particles > 5.0um / 0.1L air:", particles_50um)
    print("Particles > 10 um / 0.1L air:", particles_100um)
    print("------------------ ---------------------")
 
    buffer = buffer[32:]

    # Update the LEDs
    led_show(aqi,numpix, 500)
    
    oled.fill(0)
    oled.text('================', 0, 0)
    oled.text('',0,7)
    oled.text('PM 1.0: ' + str(pm10_standard), 7, 17)
    oled.text('PM 2.5: ' + str(pm25_standard), 7, 27)
    oled.text('PM 10.0: ' + str(pm100_standard), 7, 37)
    oled.text('AQI: ' + str(aqi), 3, 47)
    #oled.text('================', 0, )
    oled.show()