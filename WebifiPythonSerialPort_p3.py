import serial, time, sys, signal, configparser
from threading import Thread
import Webifi_p3
import logging
import os


class SerialPort:
    def __init__(self, port):
        # configure serial port
        self._rx_callback = None
        self._parity = serial.PARITY_NONE
        self._baudrate = 115200
        self._number_of_bits = serial.EIGHTBITS
        self._stop_bits = serial.STOPBITS_ONE
        self._port = port
        self._serial = None
        self._running = False
        self._thread = None

    def set_parity(self, new_parity):
        if new_parity == 'E' or new_parity == 'e':
            self._parity = serial.PARITY_EVEN
        elif new_parity == 'O' or new_parity == 'o':
            self._parity = serial.PARITY_ODD

    def set_baudrate(self, new_baudrate):
        self._baudrate = new_baudrate

    def set_number_of_bits(self, new_number_of_bits):
        if new_number_of_bits == '7':
            self._number_of_bits = serial.SEVENBITS

    def set_stop_bits(self, new_stop_bits):
        if new_stop_bits == '2':
            self._stop_bits = serial.STOPBITS_TWO

    def set_rx_callback(self, rx_callback):
        self._rx_callback = rx_callback

    def open_serial_port(self):
        self._serial = serial.Serial(port=self._port, baudrate=self._baudrate, parity=self._parity,
                                     stopbits=self._stop_bits, bytesize=self._number_of_bits, timeout=0.25)
        # Create thread
        self._running = True
        self._thread = Thread(target=self._update)
        self._thread.start()

    def close_serial_port(self):
        self._running = False
        self._serial.close()

    def _update(self):
        while self._running:
            c = self._serial.read(1)
            if c:
                if self._rx_callback:
                    self._rx_callback(c)
        return False

    def send_data(self, data):
        if self._running:
            if type(data) is list:
                data = bytearray(data)
            data_bytes = bytearray()
            data_bytes.extend(map(ord, data))
            self._serial.write(data_bytes)


class WebifiSerialPort:
    def __init__(self, webifi_connectname, webifi_password, serial_port, encryption, use_websocket,
                 webifi_network_names, webifi_datatype, log_directory):
        self._log_directory = log_directory
        self._webifi = Webifi_p3.Webifi()
        self._webifi.set_connect_name(webifi_connectname)
        self._webifi.set_connect_password(webifi_password)
        self._webifi.set_network_names(webifi_network_names)
        self._webifi.set_connection_status_callback(self.connection_status_callback)
        self._webifi.set_data_received_callback(self.data_received_callback)
        if self._log_directory != '':
            self._webifi.enable_logging(self._log_directory, logging.DEBUG, True)
        self._webifi.name = 'Python Serial Port'
        if encryption:
            self._webifi.set_use_encryption(True)
        if not use_websocket:
            self._webifi.set_use_websocket(False)
            print("Connection type: Long polling")
        else:
            print("Connection type: WebSocket")
        self._send_data_collected = ""
        self._webifi.start()
        self._running = True
        self._datatype = webifi_datatype
        self._thread = Thread(target=self._collect_data)
        self._thread.start()
        self._serial_port = serial_port
        self._serial_port.set_rx_callback(self.data_received)
        print("Press Ctrl+C to quit")
        signal.signal(signal.SIGINT, self.signal_handler)
        while self._running:
            time.sleep(0.1)

    def signal_handler(self, signal, frame):
        self._webifi.close_connection(True)
        self._running = False
        self._serial_port.close_serial_port()
        print('Program stopped')
        sys.exit(0)

    def _collect_data(self):
        while self._running:
            if len(self._send_data_collected) > 0:
                send_data = Webifi_p3.CreateSendData()
                send_data.data = self._send_data_collected
                send_data.data_type = self._datatype
                self._webifi.send_data(send_data)
                self._send_data_collected = ""
            time.sleep(0.01)
        return False

    @staticmethod
    def connection_status_callback(connected):
        if connected:
            print('\nConnection successful\n')
        else:
            print('\nConnection failed\n')

    def data_received_callback(self, data, data_type, from_who):
        self._serial_port.send_data(data)
        # print(data)

    # callback which will be called by serial port when data is received
    def data_received(self, c):
        self._send_data_collected += c.decode()
        # print(c)

if __name__ == "__main__":
    # see if the user specified a settings file
    if len(sys.argv) == 2:
        settings_filename = sys.argv[1]
    else:
        settings_filename = "settings.ini"
    if not os.path.isfile(settings_filename):
        print('Error: Could not load settings file: ' + settings_filename)
        sys.exit()
    network_names_option = "network"
    config = configparser.ConfigParser()
    config.read(settings_filename)
    connection_list = config.options("WebifiConnectionDetails")
    param_webifi_connectname = config.get("WebifiConnectionDetails", "connectname")
    param_webifi_password = config.get("WebifiConnectionDetails", "password")
    param_webifi_datatype = config.get("WebifiConnectionDetails", "datatype")
    param_webifi_encryption = False
    if config.get("WebifiConnectionDetails", "encryption") == "1":
        param_encryption = True
    param_webifi_use_websocket = True
    if config.get("WebifiConnectionDetails", "useWebsocket") == "0":
        param_webifi_use_websocket = False
    param_webifi_log_directory = config.get("WebifiConnectionDetails", "logDirectory")
    param_webifi_network_names = []
    for item in connection_list:  # search for network names
        if item[:len(network_names_option)] == network_names_option:
            param_webifi_network_names.append(config.get("WebifiConnectionDetails", item))
    param_serial_port_name = config.get("SerialPortSettings", "serport")
    param_parity = config.get("SerialPortSettings", "parity")
    param_baudrate = config.get("SerialPortSettings", "baudrate")
    param_number_of_bits = config.get("SerialPortSettings", "numbits")
    param_stop_bits = config.get("SerialPortSettings", "stopbits")
    serial_port = SerialPort(param_serial_port_name)
    serial_port.set_parity(param_parity)
    serial_port.set_baudrate(param_baudrate)
    serial_port.set_number_of_bits(param_number_of_bits)
    serial_port.set_stop_bits(param_stop_bits)
    serial_port.open_serial_port()
    webifi = WebifiSerialPort(param_webifi_connectname, param_webifi_password, serial_port, param_webifi_encryption,
                              param_webifi_use_websocket, param_webifi_network_names, param_webifi_datatype,
                              param_webifi_log_directory)
    print("Program finished")
