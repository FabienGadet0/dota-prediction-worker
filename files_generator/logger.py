import termcolor
from enum import Enum
import os

to_color = {
    'INFO': 'white',
    'DEBUG': 'blue',
    'ERROR': 'red',
    'SUCCESS': 'green',
    'WARNING': 'magenta',
    'FILE': 'green',
    'EXCEPTION': 'yellow'
}

flag = {
    'INFO': '[INFO]',
    'DEBUG': '[DEBUG_STEP]',
    'ERROR': '[KO]',
    'EXCEPTION': '[EXCEPT]',
    'SUCCESS': '[OK]',
    'FILE': '[FILE]',
    'WARNING': '[WAR]'}


def log(l, message):
    if l not in to_color:
        l = 'INFO'
    if l == 'EXCEPTION':
        raise(Exception(flag[l] + ' ' + message))
    if l == 'DEBUG' and os.getenv("DEBUG", "false").lower() != "true":
            return 
    termcolor.cprint(flag[l] + ' ' + message, to_color[l])
