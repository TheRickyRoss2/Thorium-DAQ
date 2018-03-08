import sys
from copy import deepcopy

import ROOT


def dump_data(output_filename, current_trigger, current_voltage, list_events, channels):
    """
    Writes data to file as a vectorized representation of the
    events->channels->voltage readings
    :return: None
    """

    tree_file = ROOT.TFile(
        "{}_{}_trig_{}V.root".format(
            output_filename,
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

    if channels[0]:
        tree.Branch("w1", vector_voltage_1)
        tree.Branch("t1", vector_time_1)
    if channels[1]:
        tree.Branch("w2", vector_voltage_2)
        tree.Branch("t2", vector_time_2)
    if channels[2]:
        tree.Branch("w3", vector_voltage_3)
        tree.Branch("t3", vector_time_3)
    if channels[3]:
        tree.Branch("w4", vector_voltage_4)
        tree.Branch("t4", vector_time_4)

    for event in list_events:
        if event[0]:
            for data in event[0]:
                vector_time_1.push_back(data[0])
                vector_voltage_1.push_back(data[1])
        if event[1]:
            for data in event[1]:
                vector_time_2.push_back(data[0])
                vector_voltage_2.push_back(data[1])
        if event[2]:
            for data in event[2]:
                vector_time_3.push_back(data[0])
                vector_voltage_3.push_back(data[1])
        if event[3]:
            for data in event[3]:
                vector_time_4.push_back(data[0])
                vector_voltage_4.push_back(data[1])

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


if __name__ == "__main__":
    events = []
    channels = [False] * 4
    list_channels = [None] * 4
    cur_channel = 0
    counter = 0
    appended = False
    with open(sys.argv[1]) as input_file:
        waveform = []
        for line in input_file:
            if "5.005" in line:
                x = 0
                pass
            if counter == 1002:
                list_channels[cur_channel] = deepcopy(waveform)
                counter = 0
                waveform = []
            if "DT" in line:
                continue
            if "CHANNEL:1" in line:
                cur_channel = 0
                channels[0] = True
                appended = False
                continue
            if "CHANNEL:2" in line:
                cur_channel = 1
                channels[1] = True
                appended = False
                continue
            if "CHANNEL:3" in line:
                cur_channel = 2
                channels[2] = True
                appended = False
                continue
            if "CHANNEL:4" in line:
                cur_channel = 3
                channels[3] = True
                appended = False
                continue
            if "," in line:
                waveform.append((float(line.split(",")[0]), float(line.split(",")[1])))
                counter = counter + 1
                appended = False
                continue

            if len(line) < 2 and not appended:
                events.append(list_channels)
                list_channels = [None] * 4
                appended = True
                continue
            else:
                appended = False
    print(len(events))
    dump_data("_".join(sys.argv[1].split("_")[0:5]), "user", "200", events, channels)
