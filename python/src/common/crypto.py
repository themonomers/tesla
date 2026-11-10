import nacl.pwhash
import getpass
import argparse

from common.argutil import CustomHelpFormatter
from nacl.secret import SecretBox
from nacl.utils import random

##
# Read an unencrypted file and encrypt it.
#
# author: mjhwa@yahoo.com
##
def encrypt_file(read_fn, write_fn, key_fn):
  # Check to see that the filenames are different
  if read_fn == write_fn:
    raise Exception('Read and write filenames cannot be the same')

  # Open unencrypted file
  f = open(read_fn, 'rb')
  message = f.read()
  f.close()

  # Encrypt file
  encrypt(message, write_fn, key_fn)


##
# Write unencrypted text to an encrypted file.
#
# author: mjhwa@yahoo.com
##
def encrypt(message, write_fn, key_fn):
  # Check type to convert to bytes
  if not isinstance(message, bytes):
    message = message.encode('utf-8')

  # Encrypt data
  encrypted = get_box(key_fn).encrypt(message)

  # Write encrypted file, allowing overwriting of existing file
  write_file(write_fn, encrypted, False)


##
# Decrypt an encrypted file.
#
# author: mjhwa@yahoo.com
##
def decrypt(read_fn, key_fn):
  # Open encrypted file
  f = open(read_fn, 'rb')
  message = f.read()
  f.close()

  # Decrypt data
  return get_box(key_fn).decrypt(message).decode('utf-8')


##
# Derive a deterministic key using a password and a fixed, unchanging sequence 
# of 16 bytes used as the parameter in password hashing or key derivation 
# functions in PyNaCl.
#
# author: mjhwa@yahoo.com
##
def generate_password_key(write_fn, ss_fn):
  password = getpass.getpass(prompt='Enter your key generator password: ')

  # A static salt used to ensure the same password always yields the same key
  # (Keep this salt safe, but it doesn't need to be as highly secret as the key itself)
  static_salt_key = open(ss_fn, 'rb')
  static_salt = static_salt_key.read()[:16]
  static_salt_key.close()

  # Derive the 32-byte key deterministically
  key = nacl.pwhash.argon2id.kdf(
      SecretBox.KEY_SIZE,
      password.encode(),
      static_salt,
      opslimit=nacl.pwhash.OPSLIMIT_INTERACTIVE,
      memlimit=nacl.pwhash.MEMLIMIT_INTERACTIVE
  )

  # Write key, but not allow overwriting of existing key
  write_file(write_fn, key)


##
# Generate a secure 32-byte random key based on PyNaCl.
#
# author: mjhwa@yahoo.com
##
def generate_random_key(write_fn):
  key = random(SecretBox.KEY_SIZE)

  # Write key, but not allow overwriting of existing key
  write_file(write_fn, key)


##
# Retrieve the PyNaCl secret box with a key.
#
# author: mjhwa@yahoo.com
##
def get_box(key_fn):
  key_file = open(key_fn, 'rb')
  key = key_file.read()
  key_file.close()

  return SecretBox(key)


##
# Centralized file writing with default exclusive creation mode to
# prevent overwriting an existing file.
#
# author: mjhwa@yahoo.com
##
def write_file(write_fn, content, check_file=True):
  mode = 'xb'
  if check_file is False:
    mode = 'wb'

  f = open(write_fn, mode)
  f.write(content)
  f.close()


def main(parser):
  args = parser.parse_args()

  if args.decrypt:
    key_fn = args.decrypt[0]
    source_fn = args.decrypt[1]
    print(decrypt(source_fn, key_fn))
  elif args.encrypt:
    key_fn = args.encrypt[0]
    input_fn = args.encrypt[1]
    target_fn = args.encrypt[2]
    encrypt_file(input_fn, target_fn, key_fn)
  elif args.generate_password_key:
    write_fn = args.generate_password_key[0]
    ss_fn = args.generate_password_key[1]
    generate_password_key(write_fn, ss_fn)
  elif args.generate_random_key:
    write_fn = args.generate_random_key[0]
    generate_random_key(write_fn)
  else:
    parser.print_help()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    prog='crypto.py',
    description='Encryption and decryption functions for sensitive files.',
    formatter_class=CustomHelpFormatter
  )
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
    '-d', 
    '--decrypt', 
    help='decrypt file and print contents; KEY_FILE is the location and filename of the encryption '
         'key, SOURCE_FILE is the location and filename to decrypt', 
    nargs=2,
    metavar=('KEY_FILE', 'SOURCE_FILE')
  )
  group.add_argument(
    '-e', 
    '--encrypt', 
    help='read a file and encrypt its contents in a new file; KEY_FILE is the location and filename '
         'of the encryption key, INPUT_FILE is the location and filename of the un-encrypted file to '
         'read from, TARGET_FILE is the location and filename of the encrypted file to write to', 
    nargs=3,
    metavar=('KEY_FILE', 'INPUT_FILE', 'TARGET_FILE')
  )
  group.add_argument(
    '-p', 
    '--generate_password_key', 
    help='derive a deterministic key using a password based on PyNaCl; KEY_FILE is the location and filename '
         'of the generated encryption key, STATIC_SALT_FILE is the location and filename of the fixed, '
         'random byte string (the salt) required to deterministically derive the exact same encryption key '
         'from a passphrase', 
    nargs=2,
    metavar=('KEY_FILE', 'STATIC_SALT_FILE')
  )
  group.add_argument(
    '-r', 
    '--generate_random_key', 
    help='generate a secure 32-byte random key based on PyNaCl; KEY_FILE is the location and filename '
         'of the generated encryption key', 
    nargs=1,
    metavar=('KEY_FILE')
  )

  main(parser)