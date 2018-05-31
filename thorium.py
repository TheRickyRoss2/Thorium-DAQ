#!/usr/bin/python3
__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

import argparse
import configparser
import gc
import io
import sys
import time
from re import sub

import ROOT

from caen import Caen
from lecroy import Oscilloscope
from lecroy_support import readTrc


class DaqRunner(object):
    """
    Data Acqusition state machine
    """
    list_events = []
    list_currents = []
    list_times = []

    def __init__(self, scope_ip, num_events, active_channels, output_filename,
                 caen_ip, volt_list, caen_channel, using_caen,
                 trigger_list):
        """
        Initializer function for the DAQ state machine
        :param ip_address: IP address of scope
        :param num_events: number of event that we would like
        :param channel_mask: Which channels we want in hex
        :param output_filename: file to dump data to
        """

        self.use_caen = using_caen
        if self.use_caen:
            self.caen = Caen(caen_ip)
            self.caen_channel = caen_channel
            if "ON" not in self.caen.status_check(self.caen_channel):
                self.caen.enable_output(self.caen_channel, True)

        self.volt_list = volt_list
        self.trigger_list = trigger_list
        self.output_filename = output_filename
        self.num_events = num_events
        self.scope = Oscilloscope(scope_ip)
        self.channels = active_channels
        self.dt = 0
        # print(self.scope.inst.query("C2:INSPECT? HORIZ_OFFSET;"))

        for volt in self.volt_list:
            if self.trigger_list is not None:
                for trigger in self.trigger_list:

                    print("Trig {}".format(trigger))
                    self.scope.arm_trigger("1", "NEG", str(float(volt) / 1000.))

                    if self.use_caen:
                        if self.caen.overcurrent():
                            break
                        self.caen.set_output(self.caen_channel, volt)
                        time.sleep(5)
                        while "RAMP UP" in self.caen.status_check(self.caen_channel):
                            pass

                    self.get_timebase()
                    self.get_events()
                    self.dump_data(str(abs(float(trigger))) + "mV", volt.strip())

            else:
                if self.use_caen:
                    if self.caen.overcurrent():
                        break
                    self.caen.set_output(self.caen_channel, volt)
                    time.sleep(5)
                    while "RAMP UP" in self.caen.status_check(self.caen_channel):
                        pass
                self.get_timebase()
                time_start = time.time()
                self.get_events()
                print("{} s/wfm".format((time.time() - time_start) / 100.0))
                self.dump_data("user", volt.strip())

        if self.use_caen:
            self.caen.set_output(self.caen_channel, "0")
            time.sleep(5)
            while "RAMP DOWN" in self.caen.status_check(self.caen_channel):
                pass
            self.caen.close()
            with open("{}_currents.csv".format(self.output_filename), "w") as currents_file:
                for idx, volt in enumerate(self.volt_list):
                    currents_file.write("Begin,{},{}\n".format(volt, self.list_currents[idx][0]))
                    currents_file.write("Middle,{},{}\n".format(volt, self.list_currents[idx][1]))
                    currents_file.write("End,{},{}\n".format(volt, self.list_currents[idx][2]))

        with open("{}_times.txt".format(self.output_filename), "w") as times_file:
            for item in self.list_times:
                times_file.write("{}\n".format(str(item)))

        print("Acqusition complete")
        self.scope.close()

    def dump_data(self, current_trigger, current_voltage):
        """
        Writes data to file as a vectorized representation of the
        events->channels->voltage readings
        :return: None
        """

        tree_file = ROOT.TFile(
            "{}_{}_trig_{}V.root".format(
                self.output_filename,
                current_trigger,
                current_voltage),
            "recreate"
        )

        tree = ROOT.TTree("wfm", "tree with events/wfms")

        vector_voltage_1 = ROOT.vector("double")()
        vector_time_1 = ROOT.vector("double")()
        vector_voltage_2 = ROOT.vector("double")()
        vector_time_2 = ROOT.vector("double")()
        vector_voltage_3 = ROOT.vector("double")()
        vector_time_3 = ROOT.vector("double")()
        vector_voltage_4 = ROOT.vector("double")()
        vector_time_4 = ROOT.vector("double")()

        if self.channels[0]:
            tree.Branch("w1", vector_voltage_1)
            tree.Branch("t1", vector_time_1)
        if self.channels[1]:
            tree.Branch("w2", vector_voltage_2)
            tree.Branch("t2", vector_time_2)
        if self.channels[2]:
            tree.Branch("w3", vector_voltage_3)
            tree.Branch("t3", vector_time_3)
        if self.channels[3]:
            tree.Branch("w4", vector_voltage_4)
            tree.Branch("t4", vector_time_4)

        for event in self.list_events:
            if event[0]:
                for idx in range(len(event[0][0])):
                    vector_time_1.push_back(event[0][0][idx])
                    vector_voltage_1.push_back(event[0][1][idx])
            if event[1]:
                for idx in range(len(event[1][0])):
                    vector_time_2.push_back(event[1][0][idx])
                    vector_voltage_2.push_back(event[1][1][idx])
            if event[2]:
                for idx in range(len(event[2][0])):
                    vector_time_3.push_back(event[2][0][idx])
                    vector_voltage_3.push_back(event[2][1][idx])
            if event[3]:
                for idx in range(len(event[3][0])):
                    vector_time_4.push_back(event[3][0][idx])
                    vector_voltage_4.push_back(event[3][1][idx])

            tree.Fill()
            vector_time_1.clear()
            vector_time_2.clear()
            vector_time_3.clear()
            vector_time_4.clear()
            vector_voltage_1.clear()
            vector_voltage_2.clear()
            vector_voltage_3.clear()
            vector_voltage_4.clear()

        tree_file.Write()
        tree_file.Close()

        self.list_events.clear()
        gc.collect()

    def get_events(self):
        """
        Gets event for requested channels from oscilloscope
        :return: List of channels and their voltage values
        """
        start_time = 0
        end_time = 0
        wfm_counter = 0
        sublist_currents = []
        if self.use_caen:
            sublist_currents.append(self.caen.read_current())

        """
        for position in range(len(self.positions)):
            self.set_timebase(200, "us")
            self.change_positions()
            self.set_timebase(5, "ns")
            self.scope.arm_trigger("EX", "POS", "0.1")
        """

        for event in range(int(self.num_events)):
            list_channel_wfms = [None] * 4
            if event % 100 == 0:
                print("On event {}".format(event))
            if event == int(self.num_events) // 2 and self.use_caen:
                sublist_currents.append(self.caen.read_current())

            # event_wfm = self.scope.get_waveforms()
            time = 0
            self.scope.inst.write("ARM; WAIT;")
            for channel_number, active_channel in enumerate(self.channels):
                if active_channel:
                    x, y, time = self.get_wfm(active_channel + 1)
                    list_channel_wfms[active_channel] = (x, y)
                    # command_result += self.scope.inst.query("C{}:INSPECT? SIMPLE;".format(str(channel_number + 1)))

            self.list_events.append(list_channel_wfms)

            self.list_times.append("EVENT:{},".format(str(event)) + str(time))

        if self.use_caen:
            sublist_currents.append(self.caen.read_current())
            self.list_currents.append(sublist_currents)

    def get_timebase(self):
        """
        Retrieves the active horizontal timebase of the scope
        :return: float representation of the timebase
        """

        raw_dt = self.scope.inst.query("C2:INSPECT? HORIZ_INTERVAL")
        dt = float(raw_dt.split(":")[2].split(" ")[1])
        self.dt = dt

    def set_timebase(self, secs, unit):
        self.scope.inst.write("TDIV {}{}".format(secs, unit))
        self.scope.inst.query("*OPC?")

    def convert_to_vector(self, values):
        """
        Helper function for converting the values from the oscilloscope
        to a vectorized quantity suitable for translation to a root TTree
        :param values: Raw oscilloscope voltage values
        :return: Vectorized representation of oscilloscope values
        """
        list_channel_wfms = [None] * 4
        cur_channel = -1
        time_idx = 0

        if values is not None:
            waveform = []

            for line in values.split("\n"):
                # print("Parsing line=>"+line)
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
                            waveform.append((self.dt * time_idx, volt))
                            time_idx += 1
                        except:
                            pass
            list_channel_wfms[cur_channel] = waveform

        return list_channel_wfms

    def change_positions(self):
        self.scope.arm_trigger("C1", "POS", "1")
        self.scope.write("ARM; WAIT;")
        self.scope.inst.timeout = 60000 * 5
        self.scope.query("*OPC?")

    def get_wfm(self, ch):
        self.scope.inst.write("C{}:WF?;".format(ch))
        self.write_tmp_wfm(io.BytesIO(self.scope.inst.read_raw()))
        x, y, time = readTrc("tmp.wfm")
        return x, y, time

    def write_tmp_wfm(self, stream):
        with open("tmp.wfm", 'wb') as f:
            f.write(stream.read())


def main():

    # Info section
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

    # Command argument parsing
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
        args.outfile = "latest_daq"

    # Config file loading
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read_file(open(args.config))
    active_channels = []
    for num_channel in range(1, 5):
        active_channels.append(config.getboolean("lecroy", "read_ch{}".format(num_channel)))
    lecroy_ip = config.get("lecroy", "ip")
    scanning_trigger = config.getboolean("lecroy", "scan_trigger")
    trigger_values = None
    if scanning_trigger:
        trigger_values = config.get("lecroy", "trigger_values").split(",")
    caen_ip = config.get("caen", "ip")
    volt_list = config.get("caen", "volts").split(",")
    caen_channel = config.get("caen", "step_channel")
    using_caen = config.getboolean("caen", "use")
    num_events = config.get("daq", "events")

    # DAQ Logic Control

    daq = DaqRunner(lecroy_ip, num_events, active_channels,
                    args.outfile,
                    caen_ip, volt_list, caen_channel, using_caen,
                    trigger_values
                    )


if __name__ == "__main__":
    main()
