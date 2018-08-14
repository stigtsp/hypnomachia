#this is my horribly coded but thoroughly debugged GUI
#it'll work but I'm writing the core functions into a separate library
#with better comments and clearer code flow
#This is spaghetti code. I have verified that it controls the device
#accurately with an oscilloscope. The GUI also reflects the artifacts
#that appear in the device's output waveform as frequency increases  ^.^

whichport = "/dev/ttyACM1"

#certified tested + functional 2017-02-26 04h55
#SYSTEM DEVELOPED ON SOFTWARE VERSIONS:
# * Arduino 1.8.1
# * Python 3.2.5
# * PySerial 2.6
# * PyGame 1.9.2pre
# * SYSTEM DEVELOPED ON ARDUINO HARDWARE: 
# * "MINI USB Nano V3.0 ATmega328P CH340G 5V 16M"
# */ <- lol C comment fragments

#assume 512 microseconds / sample!
#main loop iterates every 65.536 ms (approximately 15.25 FPS)
import random, sys, math, time, serial, argparse, threading

from time import sleep
#from pygame.locals import *
from pythonosc import osc_message_builder, udp_client, osc_server, dispatcher
from queue import Queue

#########OSC SEND  ##########


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=7400, help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

###############################

def MaxIn(unused_addr, args, MaxAmp):
    print(MaxAmp)

parser2 = argparse.ArgumentParser()
parser2.add_argument("--ip", default="127.0.0.1",help="The ip to listen on")
parser2.add_argument("--port",type=int, default=7401, help="The port to listen on")
parser2.add_argument("--serial", default="", help="Arduino serial port")
args2 = parser2.parse_args()

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/AmpIn", MaxIn, "MaxAmp")

#server = osc_server.ThreadingOSCUDPServer((args.ip, args2.port), dispatcher)
#print("Serving on {}".format(server.server_address))
#########





#generate waveform produces sine, square, triangle, ramp_up
#offset = dc bias


def generate_wave_points(waveform,frequency,amplitude,offset):
    print("generate_wave_points()")
    if(frequency > 976.6):
        frequency = 976.5625
    if(frequency < 0.01):
        frequency = 0.01
    if(amplitude > 2.002):
        amplitude = 2.001
    if(amplitude < 0):
        amplitude = 0
    if(offset > 2.002):
        offset = 2.001
    if(offset < -2.002):
        offset = -2.001
    samples_per_cycle = int(round(1/(float(frequency) * .000512)))
    wave_list = [0]* samples_per_cycle
    if(waveform == "sine"):
        for x in range (0, samples_per_cycle):
            wave_list[x] = amplitude*(math.sin(2*(math.pi)*(x/samples_per_cycle))) + offset
        wave_list[samples_per_cycle - 1] = (wave_list[0] + wave_list[samples_per_cycle - 2])/2.0

    for x in range(0, len(wave_list)):
        if(wave_list[x] > 2.002): #check positive limit
            wave_list[x] = 2.001
        if(wave_list[x] < -2.002):#check negative limit
            wave_list[x] = -2.001

    return wave_list




#this function converts mA values to appropriate DAC write values
def mA_2_DAC_write(value_in_mA):
    if(value_in_mA > 2.002): #check positive limit
        value_in_mA = 2.001
    if(value_in_mA < -2.002):#check negative limit
        value_in_mA = -2.001
    dacwrite = (int(round(((16383*1.0866)/5)*(2.5-value_in_mA)))).to_bytes(2,byteorder="big",signed=False)
    #That horrible line of code converts mA values into correct format
    #for the DAC. First it runs the values through the linear equation
    #that converts them to appropriate DAC values, then it ensures the
    #data are formatted in 16-bit unsigned integers.
    return dacwrite

#This function fills half of the 0.131072 seconds of buffer on the device.
#It requires a list of 128 values in mA;
#   output sample rate: one value per 512us.  

def tx_128_mA_values(listof128_values_in_mA):      
    data_to_transmit = [0] * 128 
    for x in range(0, 128):
        data_to_transmit[x] = mA_2_DAC_write(listof128_values_in_mA[x])
    data_sent = 0
    while (data_sent < 1):
        if (ser.inWaiting() > 0):
            print("tx_128_mA_values writing 0-128")
            for x in range(0, 128):
                ser.write(data_to_transmit[x])

                #########OSC##########
                client.send_message("/filter", str(data_to_transmit[x]))
                #time.sleep(1)
                ###############################
            ser.read(ser.inWaiting())
            data_sent += 1
    return

def initializebuffer(): #loads the device's buffer with "output zero mA" commands
    print("initializebuffer starting")
    for x in (0,256):
        print("initializebuffer: " + str(x))
        ser.write(mA_2_DAC_write(0.0))
    print("initializebuffer done")
    return


####### COMUNICAZIONE CON ARDUINO ###################################################################
    

ser = serial.Serial(whichport, 115200) # Establish the connection on a specific port
sleep(2)    #wait 2 seconds for the connection to settle

### ON & OFF TACS ####

global halted
halted = 0

### KIND OF WAVE ####


global which_mode
which_mode = "sine"

### FREQUENCY ####

global frequency
frequency = 40.

### AMPLITUDE ####


global amplitude
amplitude = 0.5

### DC BIAS ####


global dc_bias
dc_bias = 0.0


global wave_points
wave_points = generate_wave_points("sine", 0.1, 0.5, 0)

initializebuffer()

def main():
    print("main()")
    ticks = 0
    while True:
        print("main: start iter")
        listlength = len(wave_points)
        txlist = [0]*128
        for x in range (0, 128):
            if(halted == 0):
                txlist[x] = wave_points[(ticks + x)% listlength]
            else:
                txlist[x] = 0

        print("main: tx_128_mA_values")
        tx_128_mA_values(txlist) #if this function is called often enough it'll guarantee 65.5ms for each iteration of the loop

        args = parser.parse_args()

        ticks += 128
        if((ticks % listlength) == 0):
            ticks = 0

# def Loop2():
#     server.serve_forever()

print("End - starting stuff")
main()

