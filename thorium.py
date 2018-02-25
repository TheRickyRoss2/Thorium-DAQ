__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

import argparse
import configparser
import sys
import time
from copy import deepcopy
from queue import Queue
from re import sub

from caen import Caen
from lecroy import Oscilloscope

queue_stop = Queue()


class DaqRunner:
    """
    Data Acqusition state machine
    """
    list_events = []

    def __init__(self, scope_ip, num_events, active_channels, output_filename, stop_queue,
                 caen_ip, volt_list, caen_channel
                 ):
        """
        Initializer function for the DAQ state machine
        :param ip_address: IP address of scope
        :param num_events: number of event that we would like
        :param channel_mask: Which channels we want in hex
        :param output_filename: file to dump data to
        """

        self.caen = Caen(caen_ip)
        self.volt_list = volt_list
        self.output_filename = output_filename
        self.num_events = num_events
        self.scope = Oscilloscope(scope_ip)
        self.channels = active_channels
        self.dt = 0
        self.caen_channel = caen_channel
        self.stop_queue = stop_queue

        if "ON" not in self.caen.status_check(self.caen_channel):
            self.caen.enable_output(self.caen_channel, True)

        for volt in self.volt_list:

            self.caen.set_output(self.caen_channel, volt)
            time.sleep(5)
            while "RAMP UP" in self.caen.status_check(self.caen_channel):
                pass

            self.get_timebase()
            self.get_events()
            self.dump_data(volt)
        self.caen.set_output(self.caen_channel, "0")
        print("Acqusition complete")
        while "RAMP DOWN" in self.caen.status_check(self.caen_channel):
            pass
        self.scope.close()
        self.caen.close()

    def dump_data(self, volt):
        """
        Writes data to file as a vectorized representation of the
        events->channels->voltage readings
        :return: None
        """

        print("dumping data")
        output_file = open(self.output_filename + "_{}V".format(volt), 'w')
        for event_num, event in enumerate(self.list_events):
            for channel_num, channel in enumerate(event):
                if channel:
                    output_file.write(str(event_num) + ";CH" + str(channel_num + 1) + "\n")
                else:
                    continue
                for entry in channel:
                    output_file.write(str(entry[0]) + "," + str(entry[1]) + "\n")
                output_file.write("\n\n")

        output_file.close()

    def get_events(self):
        """
        Gets event for requested channels from oscilloscope
        :return: List of channels and their voltage values
        """

        for event in range(self.num_events):
            if not self.stop_queue.empty():
                print("STOPPING DAQ")
                return

            # event_wfm = self.scope.get_waveforms()
            command_payload = ""
            for channel_number, active_channel in enumerate(self.channels):
                if active_channel:
                    command_payload += "C{}:INSPECT? SIMPLE;".format(channel_number)
            self.list_events.append(
                self.convert_to_vector(
                    self.dt,
                    self.scope.inst.query(command_payload),
                    self.channels
                )
            )

    def get_timebase(self):
        """
        Retrieves the active horizontal timebase of the scope
        :return: float representation of the timebase
        """

        raw_dt = self.scope.inst.query("C2:INSPECT? HORIZ_INTERVAL")
        dt = float(raw_dt.split(":")[2].split(" ")[1])
        print("dt:" + str(dt))
        self.dt = dt

    def convert_to_vector(self, dt, values, channels):
        """
        Helper function for converting the values from the oscilloscope
        to a vectorized quantity suitable for translation to a root TTree
        :param dt: Value of each dt in points
        :param values: Raw oscilloscope voltage values
        :param channels: which channels are active
        :return: Vectorized representation of oscilloscope values
        """
        list_channel_wfms = [None] * 4
        cur_channel = -1
        time_idx = 0

        if values is not None:
            waveform = []

            for line in values.split("\r\n"):
                for entry in line.split(" "):
                    if ":" in entry:
                        if cur_channel >= 0:
                            list_channel_wfms[cur_channel] = waveform
                            waveform = []
                            time_idx = 0
                        cur_channel = int(sub('[^0-9]', '', entry)) - 1
                    else:
                        try:
                            volt = float(entry.strip())
                            waveform.append((dt * time_idx, volt))
                            time_idx += 1
                        except:
                            pass
            list_channel_wfms[cur_channel] = deepcopy(waveform)

        return list_channel_wfms


if __name__ == "__main__":
    print("""Welcome to
    
 ________  __                            __                         
/        |/  |                          /  |                        
$$$$$$$$/ $$ |____    ______    ______  $$/  __    __  _____  ____  
   $$ |   $$      \  /      \  /      \ /  |/  |  /  |/     \/    \ 
   $$ |   $$$$$$$  |/$$$$$$  |/$$$$$$  |$$ |$$ |  $$ |$$$$$$ $$$$  |
   $$ |   $$ |  $$ |$$ |  $$ |$$ |  $$/ $$ |$$ |  $$ |$$ | $$ | $$ |
   $$ |   $$ |  $$ |$$ \__$$ |$$ |      $$ |$$ \__$$ |$$ | $$ | $$ |
   $$ |   $$ |  $$ |$$    $$/ $$ |      $$ |$$    $$/ $$ | $$ | $$ |
   $$/    $$/   $$/  $$$$$$/  $$/       $$/  $$$$$$/  $$/  $$/  $$/  
    """)
    print("For support or bug report submission: Please email Ric <therickyross2@gmail.com>")

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Config file with settings for DAQ")
    parser.add_argument("--outfile", help="Output filename")
    args = parser.parse_args()
    if args.config:
        print("Loading in " + args.config)
    else:
        print("No config file specified. Exiting now")
        sys.exit(1)

    if args.outfile:
        print("Saving to " + args.outfile)
    else:
        print("No output file specified. Using latest_daq.root")
        args.outfile = "latest_daq.root"


    config = configparser.RawConfigParser(allow_no_value=True)
    config.read_file(open(args.config))

    active_channels = []
    for num_channel in range(1, 5):
        active_channels.append(config.getboolean("lecroy", "read_ch{}".format(num_channel)))
    lecroy_ip = config.get("lecroy", "ip")
    caen_ip = config.get("caen", "ip")
    volt_list = config.get("caen", "volts").split(",")
    caen_channel = config.get("caen", "step_channel")
    num_events = config.get("daq", "events")

    """
    h = ROOT.TH1F( 'h1', 'test', 100, -10., 10.)
    f = ROOT.TFile('test.root', 'recreate')
    t = ROOT.TTree('t1', 'tree with histos')
    maxn = 10
    n = array('i', [0])
    d = array('f', maxn*[0.])
    t.Branch('mynum', n, 'mynum/I')
    t.Branch('myval', d, 'myval[mynum]/F')
    for i in range(25):
        n[0] = min(i, maxn)
        for j in range(n[0]):
            d[j] = i*0.1+j
        t.Fill()
    f.Write()
    f.Close()
    convert_to_vector(1.25e-12, open("sample4.dat").readlines())
    """

    DaqRunner(lecroy_ip, num_events, active_channels, args.outfile, queue_stop, caen_ip, volt_list, caen_channel)
    caen = Caen("192.168.2.4")
