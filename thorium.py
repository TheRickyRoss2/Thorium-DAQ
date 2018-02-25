__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

import configparser
import threading
from copy import deepcopy
from queue import Queue
from re import sub

from caen import Caen
from lecroy import Oscilloscope

queue_stop = Queue()


class get_interrupt(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pass


class daq_runner:
    """
    Data Acqusition state machine
    """
    list_events = []

    def __init__(self, scope_ip, num_events, channel_mask, output_filename, stop_queue,
                 caen_ip, volt_list
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
        self.channels = [False] * 4
        self.set_channels(channel_mask)
        self.dt = 0

        self.get_timebase()
        self.get_events()
        self.dump_data()

        self.scope.close()
        self.stop_queue = stop_queue

    def dump_data(self):
        """
        Writes data to file as a vectorized representation of the
        events->channels->voltage readings
        :return: None
        """

        print("dumping data")
        output_file = open(self.output_filename, 'w')
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

    def set_channels(self, channel_mask):
        """
        Prepares the channels for recieving data acquisition
        :param channel_mask: Hex format of channels i.e. 0x2 repesents channel 2
        :return: None
        """

        ch_idx = 0
        while channel_mask != 0:
            if channel_mask & 1:
                self.channels[ch_idx] = True
            ch_idx += 1
            channel_mask = channel_mask >> 1
        print("set channels")
        for i, d in enumerate(self.channels):
            if d:
                print(i)

    def get_events(self):
        """
        Gets event for requested channels from oscilloscope
        :return: List of channels and their voltage values
        """

        for volt in volt_list:
            self.caen.set_output(volt)
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
                    convert_to_vector(
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


def convert_to_vector(dt, values, channels):
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
    print("By: Ric Rodriguez")
    print("For support or bug report submission: Please email Ric at therickyross2@gmail.com")

    with open("config.ini") as settings:
        daq_settings = settings.read()
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read_file(open("config.ini"))

    for section in config.sections():
        print("Section: {}".format(section))
        for options in config.options(section):
            print("x {}::{}::{}".format(options, config.get(section, options), str(type(options))))
    print(config.get('caen', 'iset'))
    print(config.getboolean('lecroy', 'enable_channel1'))
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
    import time

    # daq_runner("192.168.1.5", 20, 0x2, "run.raw", queue_stop)
    caen = Caen("192.168.2.4")
    # print(caen.enable_output(channel="2", enable=True))
    print(caen.enable_output("2", enable=True))
    print(caen.set_output(channel="2", voltage="25"))
    print(caen.status_check("2"))
    time.sleep(10)
    print(caen.status_check("2"))
    while "3" in caen.status_check("2"):
        pass
    print("DONE RAMPED UP")
    print(caen.set_output(channel="2", voltage="0"))
    time.sleep(10)
    while "5" in caen.status_check("2"):
        pass
    print("DONE RAMPED DOWN")
    print(caen.enable_output("2", enable=False))

"""
    print("*"*80)
    print("TESTING LECROY")
    lecroy_scope = Oscilloscope("192.168.2.3")
    print("*"*80)
    raw_dt = lecroy_scope.inst.query("C2:INSPECT? HORIZ_INTERVAL")
    dt = float(raw_dt.split(":")[2].split(" ")[1])
    print("dt:" + str(dt))

    values = lecroy_scope.inst.query("C1:INSPECT? SIMPLE;C2:INSPECT? SIMPLE;C3:INSPECT? SIMPLE;C4:INSPECT? SIMPLE")
    print("done acquiring")
    f = open("sample4.dat", 'w')
    f.write(values)
    f.close()
    lecroy_scope.close()
    #caen_psu = Caen("169.168.2.5")
"""
