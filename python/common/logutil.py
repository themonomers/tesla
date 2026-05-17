import os
import logging
import sys
import configparser
import datetime

from logging.handlers import TimedRotatingFileHandler


##
#  A custom FileHandler that flushes data and terminates the application
#  when an ERROR level log or higher is emitted.
#
# author: mjhwa@yahoo.com
##
class ExitOnErrorHandler(logging.FileHandler):
  def emit(self, record):
    # Run the standard write operation first
    super().emit(record)
    
    # Manually flush the file internal buffers to disk
    self.flush()
    
    # Check if the log level is equal to or higher than ERROR (Level 40)
    if record.levelno >= logging.ERROR:
      sys.exit(1)


# retrieve logging configs
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.ini'))
config.sections()
values = {s:dict(config.items(s)) for s in config.sections()}
level_string = values['general']['level']
level = getattr(logging, level_string, logging.INFO)
format = values['general']['format']
datefmt = values['general']['datefmt']

# get and configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tesla.log'),  
                    level=level,
                    format=format, 
                    datefmt=datefmt)

# set custom handler for >= ERROR logging levels and log file rotation handler
handler = ExitOnErrorHandler(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tesla.log'), 
                             mode='a')
formatter = logging.Formatter(format, datefmt=datefmt)
handler.setLevel(logging.ERROR)
handler.setFormatter(formatter)
logger.addHandler(handler)

# set handler for log rotation every 30 days
handler = TimedRotatingFileHandler(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tesla.log'), 
                                   when='midnight', 
                                   interval=30,
                                   atTime=datetime.time(3, 0),
                                   backupCount=12)
handler.setLevel(level)
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.propagate = False


##
# Standard logging function.
#
# author: mjhwa@yahoo.com
##
def log():
  return logger