# High Level Analyzer
# For more information and documentation, please go to https://github.com/saleae/logic2-examples
from typing import List

base_addresses = {
    0x00: 'STATUS_BASE',
    0x01: 'GPIO_BASE',
    0x02: 'SERCOM0_BASE',
    0x08: 'TIMER_BASE',
    0x09: 'ADC_BASE',
    0x0A: 'DAC_BASE',
    0x0B: 'INTERRUPT_BASE',
    0x0C: 'DAP_BASE',
    0x0D: 'EEPROM_BASE',
    0x0E: 'NEOPIXEL_BASE',
    0x0F: 'TOUCH_BASE',
    0x10: 'KEYPAD_BASE',
    0x11: 'ENCODER_BASE',
}

actions = {
    'TOUCH_BASE': {
        0x10: 'Capacitive',
    },
    'STATUS_BASE': {
        0x01: 'HW_ID',
        0x02: 'VERSION',
        0x03: 'OPTIONS',
        0x04: 'Temperature',
        0x7F: 'SWRST',
    }
}


class WriteTransaction:
    NOT_FOUND = 'NotFound'
    base: str = ''
    action: int = ''
    start_time: float
    end_time: float

    def __init__(self, start_time):
        self.start_time = start_time

    def create_frame(self):
        new_frame = {
            'type': 'default',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'data': {
                'value': self.action
            }
        }
        return new_frame


class ReadTransaction:
    kind: str = ''
    start_time: float
    end_time: float
    address: int
    data: int = 0
    action: str

    def __init__(self, start_time, action: str):
        self.start_time = start_time
        self.action = action

    def create_frame(self):
        new_frame = {
            'type': 'default',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'data': {
                'value': self.data
            }
        }
        return new_frame


class Hla():
    is_read: bool = False
    read_transaction: ReadTransaction = None
    last_frame: dict = None
    write_transaction: WriteTransaction = None
    TEMP_UNITS = 'Temp Units'

    def __init__(self):
        '''
        '''
        pass

    def get_capabilities(self):
        '''
        '''
        return {
            'settings': {
                TEMP_UNITS: {
                    'type': 'choices',
                    'choices': ('C', 'F')
                }
            }
        }

    def set_settings(self, settings):
        '''
        '''

        if 'Temp units' in settings:
            print(settings['Units'])
            # You can do something with the number setting here
            pass

        return {
            'result_types': {
                'default': {
                    'format': '{{data.value}}'
                }
            }
        }

    def decode(self, frame):
        '''
        '''
        value = None
        if frame['type'] == 'address':
            new_frame = None
            if self.read_transaction:
                self.read_transaction.end_time = self.last_frame.get('end_time')
                new_frame = self.read_transaction.create_frame()

            elif self.write_transaction:
                self.write_transaction.end_time = self.last_frame.get('end_time')
                new_frame = self.write_transaction.create_frame()

            value = frame['data']['address'][0]
            self.is_read = (value & 0x01) == 1
            if self.is_read:
                if (self.write_transaction):
                    self.read_transaction = ReadTransaction(frame['start_time'], self.write_transaction.action)
                self.write_transaction = None
            else:
                self.write_transaction = WriteTransaction(frame['start_time'])
                self.read_transaction = None
            return new_frame

        elif frame['type'] == 'data':
            value = frame.get('data').get('data')[0]
            if self.is_read:
                if self.read_transaction:
                    self.read_transaction.data = (self.read_transaction.data << 8) | value
            else:
                if not self.write_transaction.base:
                    self.write_transaction.base = base_addresses.get(value, WriteTransaction.NOT_FOUND)
                elif self.write_transaction.base != WriteTransaction.NOT_FOUND:
                    current_actions = actions.get(self.write_transaction.base)
                    if current_actions:
                        self.write_transaction.action = current_actions.get(value, WriteTransaction.NOT_FOUND)

            self.last_frame = frame
        else:
            return None
