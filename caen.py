__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

import socket


class Caen(object):
    """
    Class for CAEN HV Power supply
    """
    test_mode = False

    def __init__(self, ip_address="", channel="2"):
        """
        Constructor for power supply object
        :param ip_address: Ethernet address of supply
        """

        self.caen_channel = channel

        if ip_address:
            # self.inst = ResourceManager().open_resource("TCPIP0::" + ip_address + "::inst0::INSTR")
            self.caen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (ip_address, 10000)
            self.caen_sock.connect(server_address)

            print(self.query("$BD:0,CMD:MON,PAR:BDNAME"))
            print(self.query("$BD:0,CMD:MON,PAR:BDFREL"))
            print(self.query("$BD:0,CMD:MON,PAR:BDSNUM"))
        else:
            print("No ip address specified; Running in test mode.")
            self.test_mode = True

    def query(self, command):
        payload = command.encode()
        self.caen_sock.sendall(payload)
        response = self.caen_sock.recv(2048)
        return response.decode()

    def check_return_status(self, return_status=""):
        """
        Checks the return status of queries
        :param return_status: Returned bytes of query
        :return: True if command was executed successfully
        """

        if "ok" not in return_status.lower():
            raise SystemError("Invalid command")
        return True

    def connection_sanity_check(self):
        return "ok" in self.query("BD:0,CMD:MON,PAR:BDNAME").lower()

    def setup_channel(self, channel, compliance):
        """
        Configure specified channel for the caen supply
        :param channel: Channel number [0-3]
        :param compliance:  compliance in uA
        :return: True if command was successful
        """

        command_format = "$BD:0,CMD:SET,CH:{},PAR:ISET,VAL:{}".format(channel, str(float(compliance)))

        if self.test_mode:
            return "TEST MODE: " + command_format

        response = self.query(command_format)
        return self.check_return_status(response)

    def set_output(self, channel, voltage):
        """
        Sets the channel output to a specified voltage
        :param channel: Channel number [0-3]
        :param voltage: Voltage level in V
        :return: True if command succeeded
        """

        command_format = "$BD:0,CMD:SET,CH:{},PAR:VSET,VAL:{}".format(channel, str(float(voltage)))

        # If testing, return string for verification
        if self.test_mode:
            return "TEST MODE: " + command_format

        # Send query to device
        response = self.query(command_format)
        # Verify command was executed successfully
        return self.check_return_status(response)

    def enable_output(self, channel, enable=True):
        """
        Enables output if true for specified channel
        :param channel: Channel number [0-3]
        :param enable: True to turn on
        :return: True if command succeeded
        """

        command_format = "$BD:0,CMD:SET,CH:{},PAR:{}".format(channel, "ON" if enable else "OFF")

        if self.test_mode:
            return "TEST MODE: " + command_format

        response = self.query(command_format)
        return self.check_return_status(response)

    def get_response_value(self, response_string):
        return response_string.split(":")[-1].strip()

    def status_check(self, step_channel):
        """
        Checks status of channel
        :return:
        """
        status_bits = ["ON", "RAMP UP", "RAMP DOWN", "IMON>=ISET", "VMON>VSET+2.5V",
                       "VMON<VSET–2.5V", "VOUT in MAXV protection", "Ch OFF via TRIP (Imon>=Iset during TRIP)",
                       "Output Power > Max", "TEMP>105°C", "Ch disabled (REMOTE Mode and Switch on OFF position)",
                       "Ch in KILL via front panel", "Ch in INTERLOCK via front panel", "Calibration Error"
                       ]
        command_format = "$BD:0,CMD:MON,CH:{},PAR:STAT".format(self.caen_channel)
        response = int(self.get_response_value(self.query(command_format)))
        status = []
        counter = 0
        while response != 0:
            if response & 0x1:
                status.append(status_bits[counter])
            response = response >> 1
            counter += 1

        return status

    def overcurrent(self):
        """
        Checks device for errors, but mainly looking for IMON>ISET
        :return: True if device checks out
        """
        response = int(self.get_response_value(self.query("$BD:0,CMD:MON,PAR:BDALARM")))
        # TODO Logic for discerning bits
        if int(self.caen_channel) & response:
            return True
        return False
        # Bits 0-3 correspond to channels; if one of these bits is set then trigger alarm

    def close(self):
        self.caen_sock.close()
