import configparser

from common.crypto import decrypt
from io import StringIO
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


##
# Retrieves dictionary of configuration values.
#
# author: mjhwa@yahoo.com
##
def get_config(read_fn, token_fn=None):
  if token_fn is not None:
    buffer = StringIO(
      decrypt(read_fn, token_fn)
    )
  else: 
    buffer = StringIO(read_fn.read_text())

  config = configparser.ConfigParser()
  config.sections()
  config.read_file(buffer)
  values = {s:dict(config.items(s)) for s in config.sections()}
  buffer.close()
  
  return values


##
# Retrieves absolute filepaths based on standardized file structure.
#
# author: mjhwa@yahoo.com
##
def get_filepath(item):
  return PROJECT_ROOT / config['file'][item]


config = get_config(PROJECT_ROOT / './configs/config.ini')
encrypted_config = get_config(get_filepath('config'), get_filepath('tesla_key'))