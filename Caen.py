from visa import ResourceManager

class Caen(object):
    """
    Class for CAEN HV Power supply
    """
    test_mode = False
    def check_return_status(self, return_status=""):
        if "ok" not in return_status.lower():
            raise SystemError("Invalid command")

    def __init__(self, ip_address=""):
        """
        Constructor for power supply object
        :param ip_address: Ethernet address of scope
        """

        if ip_address:
            self.inst = ResourceManager().open_resource("TCPIP0::" + ip_address + "::inst0::INSTR")
            print(self.inst.query("$BD:0,CMD:MON,PAR:BDNAME"))
            print(self.inst.query("$BD:0,CMD:MON,PAR:BDFREL"))
            print(self.inst.query("$BD:0,CMD:MON,PAR:BDSNUM"))
        else:
            print("No ip address specified; Running in test mode.")
            self.test_mode = True

    def setup_channel(self, channel, compliance):
        """
        Configure specified channel for the caen supply
        :param channel: Channel number [0-3]
        :param compliance:  compliance in uA
        :return: None
        """

        command_format = "$BD:0,CMD:SET,CH:{},PAR:{},VAL:{}"

        if self.test_mode:
            return "TEST MODE: " + command_format.format(channel, "ISET", str(float(compliance)))

        response = self.inst.query(command_format.format(channel, "ISET", str(float(compliance))))
        self.check_return_status(response)

    def set_output(self, channel, voltage):
        """
        Sets the channel output to a specified voltage
        :param channel: Channel number [0-3]
        :param voltage: Voltage level in V
        :return:
        """

        command_format = "$BD:0,CMD:SET,CH:{},PAR:{},VAL:{}"

        if self.test_mode:
            return "TEST MODE: " + command_format.format(channel, "VSET", str(float(voltage)))

        response = self.inst.query(command_format.format(channel, "VSET", str(float(voltage))))
        self.check_return_status(response)

    def enable_output(self, channel, enable=True):
        """
        Enables output if true for specified channel
        :param channel: Channel number [0-3]
        :param enable: True to turn on
        :return: None
        """

        command_format = "$BD:0,CMD:SET,CH:{},PAR:{}"

        if self.test_mode:
            return "TEST MODE: " + command_format.format(channel, "ON" if enable else "OFF")

        response = self.inst.query(command_format.format(channel, "ON" if enable else "OFF"))
        self.check_return_status(response)
        return



