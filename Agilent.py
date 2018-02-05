from visa import ResourceManager
from struct import unpack

class Oscilloscope(object):
    """
    Class for Keysight DSOS254A Scope
    """
    active_channels = []
    def __init__(self, ip_address):
        """
        Constructor for scope object
        Resets scope
        :param ip_address: Ethernet address of scope
        """
        self.inst = ResourceManager().open_resource("TCPIP0::" + ip_address + "::inst0::INSTR")
        print(self.inst.query("*IDN?;"))
        self.inst.write("RST;")
        self.inst.write(":WAV:FORM WORD;")

    def configure_channel(self, channel_number, volts_per_div):
        """
        Set up channel scale
        :param channel_number: 1-4 channel specifier
        :param volts_per_div: volts per div in volts
        :return: None
        """
        self.active_channels.append(channel_number)
        self.inst.write(":CHAN%s:DISP ON;".format(channel_number))
        self.inst.write(":CHAN%s:SCAL %s;".format(channel_number, str(float(volts_per_div))))

    def arm_trigger(self, channel_number, edge_slope, thresh_level):
        """
        Arms and sets up the trigger
        :param channel_number: 1-4, AUX channel specifier
        :param edge_slope: rising or falling edge
        :param thresh_level: voltage level for trigger
        :return: None
        """
        self.inst.write(":TRIG:EDGE:SOUR %s;:TRIG:EDGE:SLOP %s;".format(channel_number, edge_slope))
        self.inst.write(":TRIG:LEV %s,%s;".format(channel_number, thresh_level))

    def get_waveforms(self):

        for channel in self.active_channels:
            query_result = self.inst.query(":WAV:TYPE?;")
            print("Waveform type: %s".format(query_result))
            x_increment = self.inst.query(":WAVE:XINC?;")
            x_origin = self.inst.query(":WAV:XOR?;")
            y_increment = self.inst.query(":WAV:YINC?;")
            y_origin = self.inst.query(":WAV:YOR?;")

            self.inst.write(":WAV:STR OFF")
            raw_waveform_data = self.inst.query(":WAV:DATA?;")

            waveform_data = unpack("%db".format(len(raw_waveform_data)), raw_waveform_data)
            print("Number of data values: %d".format(len(waveform_data)))

            for point in range(0, len(waveform_data)-1):
                time_value = x_origin+(i*x_increment)
                voltage_value = (waveform_data[i]*y_increment)+y_origin
                print("Point %d: %E, %f".format(i, time_value, voltage_value))

