from enum import Enum


class Actions(Enum):
    Temperature = 'Temperature'
    Capacitive = 'Capacitive'
    HW_ID = 'HW_ID'
    VERSION = 'VERSION'
    OPTIONS = 'OPTIONS'
    SWRST = 'SWRST'


print(Actions.Temperature.name)
