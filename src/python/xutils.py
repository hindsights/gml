import new
import types
import os
import sys
import traceback
from cStringIO import StringIO
import logging

class Table(object):
    def __init__(self, d=None):
        assert(isinstance(d, dict) or d is None)
        self._d = {}
        if d:
            self._d.update(d)
    #def __setattribute__(self, name, val):
    #    self._d[name] = val
    def __delattr__(self, name):
        if name in self.d:
            del self._d[name]
    def __getattr__(self, name):
        return self._d.get(name, None)

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    enums['parse'] = lambda s: reverse.get(s, None)
    return type('Enum', (), enums)

class EnumItem(object):
    def __init__(self, enum, name, value):
        self.enum = enum
        self.name = name
        self.value = value

class Enum(object):
    def __init__(self, name, *sequential, **named):
        self.name = name
        self.values = dict(zip(sequential, range(len(sequential))), **named)
        self.items = {}
        for k, v in self.values.iteritems():
            item = EnumItem(self, k, v)
            self.items[k] = item
            # setattr(self, k, item)
            setattr(self, k, v)
    def parse(self, s, defval = None):
        return self.items.get(s, defval)


class SeqSet(object):
    def __init__(self):
        self.items = []
        self.item_index = {}
    def add(self, items):
        if isinstance(items, list):
            self.doAddMany(items)
        else:
            self.doAddOne(items)
    def doAddMany(self, items):
        for item in items:
            self.doAddOne(item)
    def doAddOne(self, item):
        if item in self.item_index:
            return
        self.items.append(item)
        self.item_index[item] = item

def execCommand(cmd):  
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text

def saySomething(s):
    if sys.platform == 'darwin':
        os.system('say ' + s)

def printException(e, lines=50):
    if lines is None:
        traceback.print_exc()
        return
    sout = StringIO()
    traceback.print_exc(None, sout)
    elines = sout.getvalue().split('\n')[-lines:]
    print('\n'.join(elines))

class Logging(object):
    loggerLevel = logging.WARNING

class Logger(object):
    def __init__(self, name):
        self.name = name
        self.syslogger = logging.getLogger(name)
    def log(self, level, *args):
        if level < Logging.loggerLevel:
            return
        argstrs = [str(arg) for arg in args]
        self.syslogger.log(level, ' '.join(argstrs))
    def debug(self, *args):
        self.log(logging.DEBUG, *args)
    def info(self, *args):
        self.log(logging.INFO, *args)
    def warning(self, *args):
        self.log(logging.WARNING, *args)
    def error(self, *args):
        self.log(logging.ERROR, *args)
    def critical(self, *args):
        self.log(logging.CRITICAL, *args)

def initLogging(level):
    Logging.loggerLevel = level
    logging.basicConfig(stream=sys.stdout, level=level, format='[%(name)s] %(message)s')

def createLogger(name):
    logger = Logger(name)
    return logger

