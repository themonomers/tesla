import os
import logging
import sys


##
# Standard logging function.
#
# author: mjhwa@yahoo.com
##
def log():
  logger = logging.getLogger(__name__)
  logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tesla.log'), 
                      level=logging.WARNING,
                      format='%(asctime)s [%(levelname)s] %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')

  if not logger.handlers:
    handler = ExitOnErrorHandler(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tesla.log'), 
                                mode='a')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setLevel(logging.ERROR)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

  return logger


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