from visa import ResourceManager

class Caen(object):
    """
    Class for CAEN HV Power supply
    """
    def check_return_status(self, return_status=""):
        if "ok" not in return_status.lower():
            raise SystemError("Invalid command")

    def __init__(self, ip_address):
        """
        Constructor for scope object
        Resets scope
        :param ip_address: Ethernet address of scope
        """
        if ip_address:
            self.inst = ResourceManager().open_resource("TCPIP0::" + ip_address + "::inst0::INSTR")
        else:
            print("No ip specified. Running in demo mode")
        print(self.inst.query("*IDN?;"))
        self.inst.timeout = 10000
        print(self.inst.query("ASET;*OPC?"))

    def setup_channel(self, channel, ):

x = Caen()
Caen.check_return_status("ok:statis")