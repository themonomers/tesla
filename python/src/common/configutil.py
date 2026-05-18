import configparser

from common.logutil import log
from common.crypto import decrypt
from common.fileutil import get_filepath
from io import StringIO


##
# Retrieves dictionary of configuration values.
#
# author: mjhwa@yahoo.com
##
def get_config():
  try:
    buffer = StringIO(
      decrypt(get_filepath('configs', 'config'), get_filepath('secrets', 'teslaKey'))
    )
    config = configparser.ConfigParser()
    config.sections()
    config.read_file(buffer)
    values = {s:dict(config.items(s)) for s in config.sections()}
    buffer.close()
    return values
  except Exception as e:
    log().error('get_config(): ' + str(e))