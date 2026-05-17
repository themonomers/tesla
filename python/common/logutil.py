import os
import logging
import logging.config
import json
import sys


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


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.json'), 'r') as f:
  config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)


##
# Standard logging function.
#
# author: mjhwa@yahoo.com
##
def log():
  return logger