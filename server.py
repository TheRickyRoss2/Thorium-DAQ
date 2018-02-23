#!/usr/bin/python3
__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium-DAQ"


import socket
import sys
from pyvisa import ResourceManager
import logging
import logging.handlers
import os


ERROR_BOARD_NOT_FOUND = -1
ERROR_BAD_COMMAND = -2
ERROR_LOST_BOARD_COMMS = -3

HOST_IP_ADDRESS = "0.0.0.0"
PORT = 10000


class SyslogBOMFormatter(logging.Formatter):
    def format(self, record):
        result = super().format(record)
        return "ufeff" + result


class Caen_control(object):
    """
    Class to control the CAEN psu over usb-serial
    """
    test = False

    def __init__(self):

        resource_manager = ResourceManager('@py')

        try:
            self.inst = resource_manager.open_resource(
                resource_manager.list_resources()[0]
            )
        except:
            print("Could not find")
            self.test = True
            return

        if "ok" in self.inst.query("BD:0,CMD:MON,PAR:BDNAME").lower():
            print("Successfully connected to CAEN psu")
        else:
            sys.exit(ERROR_BOARD_NOT_FOUND)

    def send_command(self, command):
        if self.test:
            print(command)
            return "TEST MODE"
        return self.inst.query(command)


if __name__ == "__main__":

    # Set up loggers for DAQ
    handler = logging.handlers.SysLogHandler('/dev/log')
    formatter = SyslogBOMFormatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
    root.addHandler(handler)

    # Set up socket server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (HOST_IP_ADDRESS, PORT)
    print("starting up on {} port {}".format(*server_address))
    sock.bind(server_address)
    sock.listen(1)

    caen = Caen_control()

    while True:
        print('waiting for connection')
        connection, client_address = sock.accept()
        try:
            print("connection from {}".format(client_address))
            while True:
                data = connection.recv(2048)
                print('recieved {!r}'.format(data))
                if data:
                    print('sending')
                    response = caen.send_command(data.decode())
                    connection.sendall(response.encode())
                else:
                    print("nodata")
                    break
        finally:
            connection.close()
