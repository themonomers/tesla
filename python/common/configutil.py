import os
import configparser

from common.logutil import log
from common.crypto import decrypt
from io import StringIO


##
# Retrieves dictionary of configuration values.
#
# author: mjhwa@yahoo.com
##
def get_config():
  try:
    buffer = StringIO(
      decrypt(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'config.xor'
        ),
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'tesla_private_key.pem'
        )
      )
    )
    config = configparser.ConfigParser()
    config.sections()
    config.read_file(buffer)
    values = {s:dict(config.items(s)) for s in config.sections()}
    buffer.close()
    return values
  except Exception as e:
    log().error('get_config(): ' + str(e))