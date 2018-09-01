# Imports
import argparse
from logging import info
from ZeoRawData.BaseLink import BaseLink
from ZeoRawData.Parser import Parser
import sys
from pythonosc import osc_message_builder
from pythonosc import udp_client

import time
import json

parser = argparse.ArgumentParser()
parser.add_argument("--zeo-serial", required=True, help="Serial Port for the ZEO device")
parser.add_argument("--osc-dest-port", required=True, help="UDP Port to send OSC messages to")
parser.add_argument("--osc-dest-host", required=True, help="IP/host address to send OSC messages to")

args = parser.parse_args()



link = BaseLink(args.zeo_serial)
zeoparser = Parser()

link.addCallback(zeoparser.update)
client = udp_client.SimpleUDPClient(args.osc_dest_host, int(args.osc_dest_port))

last_sleep_stage = None
last_sleep_stage_time = time.time()

def sendToOSC(s):
    global last_sleep_stage_time, last_sleep_stage
    if not s:
        return False

    for k in ['ZeoTimestamp', 'Impedance', 'SQI', 'Version', 'Waveform']:
        if s[k]:
            client.send_message("/" + k, s[k])

    if s['FrequencyBins']:
        client.send_message("/FrequencyBins", s['FrequencyBins'].values())

    if 'BadSignal' in s:
        client.send_message("/BadSignal", s['BadSignal'] or False)

    if 'SleepStage' in s:
        if s['SleepStage']:
            last_sleep_stage = s['SleepStage']
            last_sleep_stage_time = time.time()
        client.send_message("/SleepStage", str(last_sleep_stage) + " " + str(time.time() - last_sleep_stage_time))

### zeoparser.addEventCallback( ... )
zeoparser.addSliceCallback(sendToOSC)




try:
    link.start()
    while 1:
        pass
except (KeyboardInterrupt, SystemExit):
    info("Quitting...")
finally:
    sys.exit()

