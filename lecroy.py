__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

from struct import unpack

from visa import ResourceManager


class Oscilloscope(object):
    """
    Class for Lecroy WavePro Scope
    """
    active_channels = []

    def __init__(self, ip_address):
        """
        Constructor for scope object
        Resets scope
        :param ip_address: Ethernet address of scope
        """
        if not ip_address:
            print("No ip address specified. Running in test mode.")
            return
        self.inst = ResourceManager("@py").open_resource("TCPIP0::" + ip_address + "::inst0::INSTR")
        if "LECROY" in self.inst.query("*IDN?;"):
            print("Connected to LeCroy WavePro")
        self.inst.timeout = 60000
        # self.inst.write(":WAV:FORM WORD;")

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
        self.inst.write("{}:TRig_LeVel {}V;".format(channel_number, thresh_level))
        self.inst.write("{}:TRig_SLope {};".format(channel_number, edge_slope))
        self.inst.write("{}:TRIG:MODE NORM;")

    def get_waveforms(self):
        """
        NOTE: DEPRECATED DO NOT USE
        Acquires waveforms from devices
        :param None
        :return tuple (dt, voltage_values)
        """
        channel_waveforms = []

        for channel in self.active_channels:
            self.inst.write("{}:WF?;".format(channel))
            # Read formatted data back
            # Split at regex #9, and chomp off the first 9 bytes
            raw_data = self.inst.read_raw().split(b'#9')[1][9:]
            # dt is located at byte offset 176 with a size of 4 bytes
            dt = unpack('f', raw_data[176:180])[0]
            # dy is located at byte offset 160 with a size of 4 bytes
            dy = unpack('f', raw_data[156:160])[0]

            wave_source = {0: "Channel 1",
                           2: "Channel 2",
                           4: "Channel 3",
                           8: "Channel 3"}.get(unpack('i', raw_data[344][0]))

            print("dy={}".format(dy))
            print("dt={}".format(dt))

            self.inst.write("{}:WF? DAT1;".format(channel))
            # data is offset 16 bytes from header
            raw_waveform_data = self.inst.read_raw()[16:]
            print(len(raw_waveform_data))
            # for some reason chomp off the last byte? some mismatch
            values = unpack('{}i'.format(len(raw_waveform_data) // 4), raw_waveform_data[0:len(raw_waveform_data) - 1])

            # write data to csv file for debugging purposes
            f = open("out.csv", 'w')
            for idx, x in enumerate(values):
                f.write("{}, {}\n".format(idx * dt[0], x * dy[0]))
                pass
            f.close()
            channel_waveforms.append((wave_source, dt, values))
        return channel_waveforms

    def close(self):
        """
        Close visa instance
        """
        self.inst.close()
