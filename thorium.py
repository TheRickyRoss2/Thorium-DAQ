__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

import configparser
from array import array
from copy import deepcopy
from re import sub

import ROOT
import matplotlib.pyplot as plt


class daq_runner:
    """
    """
    pass


def convert_to_vector(dt, values):
    list_channel_wfms = [None] * 4
    cur_channel = -1
    time_idx = 0
    with open("sample_stripped.dat", 'w') as f:
        waveform = []
        for line in values:
            for entry in line.split(" "):
                if ":" in entry:
                    if cur_channel >= 0:
                        list_channel_wfms[cur_channel] = waveform
                        waveform = []
                        time_idx = 0
                    cur_channel = int(sub('[^0-9]', '', entry)) - 1
                    print("Current channel: " + str(cur_channel))
                else:
                    try:
                        volt = float(entry.strip())
                        waveform.append((dt * time_idx, volt))
                        time_idx += 1
                    except:
                        pass
        list_channel_wfms[cur_channel] = deepcopy(waveform)
    for channel in list_channel_wfms:
        time = []
        volt = []
        for entry in channel:
            time.append(entry[0])
            volt.append(entry[1])

        plt.plot(time, volt)
        plt.show()
        input(">")



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
