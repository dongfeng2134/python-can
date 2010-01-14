import datetime
import logging
import logging.handlers
from optparse import OptionParser
import os
import os.path
pycallgraphAvailable = True
try:
    import pycallgraph
except ImportError:
    print "Cannot import pycallgraph - call graphing function",
    print "will not be available"
    pycallgraphAvailable = False
import sys
import time
from xml.dom import minidom

from pycanlib import CAN, canlib


class _CANLoggerListener(CAN.Listener):

    def __init__(self, logger_obj):
        self.msg_list = []
        self._logger_obj = logger_obj

    def on_message_received(self, msg):
        self._logger_obj.info(msg)
        self.msg_list.append(msg)


def ParseArguments(arguments):
    parser = OptionParser(" ".join(arguments[1:]))
    parser.add_option("-c", "--channel", dest="channel",
      help="CAN channel number", default="0")
    parser.add_option("-s", "--speed", dest="speed", help="CAN bus speed",
      default="105263")
    parser.add_option("-t", "--tseg1", dest="tseg1", help="CAN bus tseg1",
      default="10")
    parser.add_option("-u", "--tseg2", dest="tseg2", help="CAN bus tseg2",
      default="8")
    parser.add_option("-w", "--sjw", dest="sjw", help="CAN bus SJW",
      default="4")
    parser.add_option("-n", "--noSamp", dest="noSamp",
      help="CAN bus sample number", default="1")
    _helpStr = "Base log file name, where log file names are"
    _helpStr += " <base>_<datestamp>_<timestamp>"
    parser.add_option("-l", "--logFileNameBase", dest="logFileNameBase",
      help=_helpStr, default="can_logger")
    parser.add_option("-p", "--logFilePath", dest="logFilePath",
      help="Log file path", default="can_logger")
    return parser.parse_args()


def CreateBusObject(options):
    _channel = int(options.channel)
    _speed = int(options.speed)
    _tseg1 = int(options.tseg1)
    _tseg2 = int(options.tseg2)
    _sjw = int(options.sjw)
    _noSamp = int(options.noSamp)
    return CAN.Bus(channel=_channel, speed=_speed, tseg1=_tseg1,
      tseg2=_tseg2, sjw=_sjw, no_samp=_noSamp)


def SetupLogging(logFilePath, logFileNameBase):
    loggerObj = logging.getLogger("can_logger")
    loggerObj.setLevel(logging.INFO)
    _logStreamHandler = logging.StreamHandler()
    _logStreamHandler2 = logging.StreamHandler()
    _logTimestamp = datetime.datetime.now()
    _dateString = _logTimestamp.strftime("%Y%m%d")
    _timeString = _logTimestamp.strftime("%H%M%S")
    logFilePath = os.path.join(os.path.expanduser("~"),
      "%s" % logFilePath, "%s_%s_%s.log" % (logFileNameBase,
      _dateString, _timeString))
    if not os.path.exists(os.path.dirname(logFilePath)):
        os.makedirs(os.path.dirname(logFilePath))
    logFile = open(logFilePath, "w")
    _logFormatter = logging.Formatter("%(message)s")
    _formatString = "%(name)s - %(asctime)s - %(levelname)s - %(message)s"
    _logFormatter2 = logging.Formatter(_formatString)
    _logStreamHandler.setFormatter(_logFormatter)
    _logStreamHandler2.setFormatter(_logFormatter2)
    loggerObj.addHandler(_logStreamHandler)
    handleLogger = logging.getLogger("pycanlib.CAN._Handle")
    handleLogger.setLevel(logging.WARNING)
    handleLogger.addHandler(_logStreamHandler2)
    busLogger = logging.getLogger("pycanlib.CAN.Bus")
    busLogger.setLevel(logging.WARNING)
    busLogger.addHandler(_logStreamHandler2)
    messageLogger = logging.getLogger("pycanlib.CAN.Message")
    messageLogger.setLevel(logging.WARNING)
    messageLogger.addHandler(_logStreamHandler2)
    return loggerObj, logFile, os.path.basename(logFilePath)


def main(arguments):
    (options, args) = ParseArguments(arguments)
    bus = CreateBusObject(options)
    (loggerObj, logFile, xmlFileName) = SetupLogging(options.logFilePath,
      options.logFileNameBase)
    _logger_listener = _CANLoggerListener(loggerObj)
    bus.add_listener(_logger_listener)
    i = 0
    try:
        bus.enable_callback()
        while True:
            time.sleep(0.001)
    except KeyboardInterrupt:
        bus.shutdown()
    for _msg in _logger_listener.msg_list:
        logFile.write("%s\n" % _msg.__str__())

if __name__ == "__main__":
    main(sys.argv)
