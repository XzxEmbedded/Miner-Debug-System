#!/usr/bin/env python2
# USBTORS485 Converter, Y-1081 USB2.0 to RS485 Converter(FT232 Chip)
# lllking: DDS238-2 ZN/S
# Author Feb 2018 xuzhenxing <xuzhenxing@canaan.creative.com>

import logging
import serial
import time
import sys

logging.basicConfig(level=logging.INFO)

# Opening the serial port
COM_PortName = "/dev/ttyUSB0"
COM_Port = serial.Serial(COM_PortName)  # Open the COM port
logging.debug('Com Port: %s, %s', COM_PortName, 'Opened')

COM_Port.baudrate = 2400                # Set Baud rate
COM_Port.bytesize = 8                   # Number of data bits = 8
COM_Port.parity   = 'N'                 # No parity
COM_Port.stopbits = 1                   # Number of Stop bits = 1

def rs485_read():
    read_data = []

    for i in range(7):
        rx_data = COM_Port.read()
        read_data.append(hex(ord(rx_data)))
    logging.info('Read Bytes: %s', read_data)

    valid_data = (int(read_data[3], 16) << 8) | int(read_data[4], 16)

    return valid_data

def rs485_write(data):
    bytes_cnt  = COM_Port.write(data)   # Write data to serial port
    logging.debug('Write Count = %d. %s ', bytes_cnt, 'bytes written')

# CRC16-MODBUS
def crc16_byte(data):
    crc = data

    for i in range(8):
        if (crc & 0x01):
            crc = (crc >> 1) ^ 0xa001
        else:
            crc >>= 1

    return crc

def crc16_bytes(data):
    crc = 0xffff

    for byte in data:
        crc = crc16_byte(crc ^ byte)

    return crc

if __name__ == '__main__':
    '''
    Device addr; func: read:0x03, write:0x10(16);
    MODBUS protocol read/write
    CRCMODBUS protocol read:
    device-id, func, start-reg-hi, start-reg-lo, data-reg-hi, data-reg-lo, crc-lo, crc-hi
    '''
    data = [0x00, 0x03, 0x00, 0x0e, 0x00, 0x01]

    lnum = 0
    dev_id = []

    with open("ip-freq-voltlevel-devid.config") as file_object:
        for line in file_object:
            lnum += 1
            if (lnum == 5):
                dev_id = line.split()

    min_id = int(dev_id[0])
    if (min_id < 1) and (min_id > 247):
        logging.info("Input minimum device ID error.")
        sys.exit()

    max_id = int(dev_id[1])
    if (max_id < 1) and (max_id > 247):
        logging.info("Input maximum device ID error.")
        sys.exit()

    if (min_id > max_id):
        logging.info("Input device ID error.")
        sys.exit(0)

    power_file = open("CGMiner_Power.log", 'w+')

    for i in range(min_id, max_id + 1):
        data[0] = i
        crc = crc16_bytes(data)
        low = int(crc & 0xff)
        high = int((crc >> 8) & 0xff)
        data.append(low)
        data.append(high)
        logging.debug('%s', data)

        rs485_write(data)
        power_data = rs485_read()
        logging.info('Device ID: %d, Power value: %d', i, power_data)
        power_file.write(str(power_data))
        power_file.write('\n')
        time.sleep(3)

    COM_Port.close()
