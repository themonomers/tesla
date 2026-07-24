import argparse

from common.argutil import CustomHelpFormatter
from itertools import cycle


##
# Simple encryption of a file, based on a key.
#
# author: mjhwa@yahoo.com
##
def encrypt_file(read_fn, write_fn, token_fn):
  # Check to see that the filenames are different
  if read_fn == write_fn:
    raise Exception('Read and write filenames cannot be the same')

  # Open unencrypted file
  f = open(read_fn, 'rb')
  message = f.read()
  f.close()

  # Encrypt file
  encrypt(message, write_fn, token_fn)


##
# Simple encryption based on a key.
#
# author: mjhwa@yahoo.com
##
def encrypt(message, write_fn, token_fn):
  # Read key
  key_file = open(token_fn, 'rb')
  key = key_file.read()
  key_file.close()

  # Check type to convert to bytes
  if not isinstance(message, bytes):
    message = message.encode('utf-8')

  # Encrypt with key
  encrypted = ''.join(chr(ord(chr(c))^ord(chr(k))) for c,k in zip(message, cycle(key)))

  # Write encrypted file
  f = open(write_fn, 'wb')
  f.write(str.encode(encrypted))
  f.close()


##
# Simple decryption based on a key.
#
# author: mjhwa@yahoo.com
##
def decrypt(read_fn, token_fn):
  # Open encrypted file
  f = open(read_fn, 'rb')
  message = f.read()
  f.close()

  # Read key
  key_file = open(token_fn, 'rb')
  key = key_file.read()
  key_file.close()

  # Decrypt with key
  return ''.join(chr(ord(chr(c))^ord(chr(k))) for c,k in zip(message, cycle(key)))


def main(parser):
  args = parser.parse_args()

  if args.decrypt:
    token_fn = args.decrypt[0]
    source_fn = args.decrypt[1]
    print(decrypt(source_fn, token_fn))
  elif args.encrypt:
    token_fn = args.encrypt[0]
    input_fn = args.encrypt[1]
    target_fn = args.encrypt[2]
    encrypt_file(input_fn, target_fn, token_fn)
  else:
    parser.print_help()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
                    prog='crypto.py',
                    description='Encryption and decryption functions for sensitive files.',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-d', 
                     '--decrypt', 
                     help='decrypt file and print contents; TOKEN_FILE is the location and filename of the encryption '
                          'key, SOURCE_FILE is the location and filename to decrypt', 
                     nargs=2,
                     metavar=('TOKEN_FILE', 'SOURCE_FILE')
                    )
  group.add_argument(
                     '-e', 
                     '--encrypt', 
                     help='read a file and encrypt its contents in a new file; TOKEN_FILE is the location and filename '
                          'of the encryption key, INPUT_FILE is the location and filename of the un-encrypted file to '
                          'read from, TARGET_FILE is the location and filename of the encrypted file to write to', 
                     nargs=3,
                     metavar=('TOKEN_FILE', 'INPUT_FILE', 'TARGET_FILE')
                    )

  main(parser)