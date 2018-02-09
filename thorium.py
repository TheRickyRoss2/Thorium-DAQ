from yaml import TagToken

__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

from caen import Caen
from lecroy import Oscilloscope
import ROOT
from array import array

import configparser

class daq_runner:
    """
    """
    pass


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
"""
