# High Level Analyzer
# For more information and documentation, please go to https://github.com/saleae/logic2-examples
from typing import List
from enum import Enum

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

TEMP_UNITS = 'Temp Units'


class Action(Enum):
    Temperature = 'Temperature'
    Capacitive = 'Capacitive'
    HW_ID = 'HW_ID'
    VERSION = 'VERSION'
    OPTIONS = 'OPTIONS'
    SWRST = 'SWRST'


actions = {
    'TOUCH_BASE': {
        0x10: Action.Capacitive,
    },
    'STATUS_BASE': {
        0x01: Action.HW_ID,
        0x02: Action.VERSION,
        0x03: Action.OPTIONS,
        0x04: Action.Temperature,
        0x7F: Action.SWRST,
    }
}


class WriteTransaction:
    NOT_FOUND = 'NotFound'
    base: str = ''
    action: Action = None
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
                'value': self.action.name if self.action else 'Unknown'
            }
        }
        return new_frame


FORMATTED_ACTIONS = [Action.Temperature]


class ReadTransaction:
    kind: str = ''
    start_time: float
    end_time: float
    address: int
    data: int = 0
    action: str
    settings: dict

    def __init__(self, start_time, action: Action, settings):
        self.start_time = start_time
        self.action = action
        self.settings = settings

    def create_frame(self):
        value = self.data
        if self.action == Action.Temperature:
            value = value / 2 ** 16
            if self.settings.get(TEMP_UNITS, 'C') == 'F':
                value = value * (9 / 5) + 32

        new_frame = {
            'type': self.action.name if self.action in FORMATTED_ACTIONS else 'default',
            'start_time': self.start_time,
            'end_time': self.end_time,
            'data': {
                'value': '{:.2f}'.format(value)
            }
        }
        return new_frame


class Hla():
    is_read: bool = False
    read_transaction: ReadTransaction = None
    last_frame: dict = None
    write_transaction: WriteTransaction = None
    settings = dict()

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
        self.settings = settings

        return {
            'result_types': {
                'default': {
                    'format': '{{data.value}}'
                },
                Action.Temperature.name: {
                    'format': '{{data.value}} ' + settings.get(TEMP_UNITS, 'C')
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
                    self.read_transaction = ReadTransaction(
                        frame['start_time'], self.write_transaction.action, self.settings)
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
                        self.write_transaction.action = current_actions.get(value)

            self.last_frame = frame
        else:
            return None
