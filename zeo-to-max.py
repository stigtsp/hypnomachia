# Imports
from ZeoRawData.BaseLink import BaseLink
from ZeoRawData.Parser import Parser

from pythonosc import osc_message_builder
from pythonosc import udp_client

import json

# Initialize
link = BaseLink("/dev/tty.usbserial-FTHBZZ4L")
parser = Parser()

# Add the Parser to the BaseLink's callback
link.addCallback(parser.update)
client = udp_client.SimpleUDPClient("127.0.0.1", 13000)

# Add your callback functions

#def linkCallbackDebug(timestamp, timestamp_subsec, version, data):
#    print("timestamp {0}, subsec {1}, version {2}, data {3}\n".format(timestamp, timestamp_subsec, version, data))

#link.addCallback(linkCallbackDebug)

def sendToOSC(s):
    print(s)
    if not s:
        return False
    for k in ['ZeoTimestamp',  'Impedance', 'SQI', 'Version', 'Waveform', 'SleepStage']:
        if s[k]:
            client.send_message("/" + k, s[k])

    if s['FrequencyBins']:
        client.send_message("/FrequencyBins", s['FrequencyBins'].values())

    if 'BadSignal' in s:
        client.send_message("/BadSignal", s['BadSignal'] or False)

            


#parser.addEventCallback(sendToOSC)
parser.addSliceCallback(sendToOSC)

# Start link
link.start()
while 1:
    pass

