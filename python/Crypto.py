import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from itertools import cycle, izip

##
# Opens a file and encrypts its contents to write to another file.  Also writes
# the private key to the file system for decryption.
#
# author: mjhwa@yahoo.com
##
def encrypt(read_fn, write_fn):
  # Check to see that the filenames are different
  if (read_fn == write_fn):
    raise Exception('Read and write filenames cannot be the same')

  # Open unencrypted file
  f = open(read_fn, 'rb')
  message = f.read()
  f.close()

  # Generate private and public keys
  private_key = rsa.generate_private_key(
    public_exponent = 65537,
    key_size = 8192,
    backend = default_backend()
  )
  public_key = private_key.public_key()

  # Store private key
  pem = private_key.private_bytes(
    encoding = serialization.Encoding.PEM,
    format = serialization.PrivateFormat.PKCS8,
    encryption_algorithm = serialization.NoEncryption()
  )
  with open(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)), 
      'private_key.pem'
    ), 
    'wb'
  ) as f:
    f.write(pem)
    f.close()

  # Encrypt with public key
  encrypted = public_key.encrypt(
    message,
    padding.OAEP(
      mgf = padding.MGF1(algorithm = hashes.SHA256()),
      algorithm = hashes.SHA256(),
      label = None
    )
  )

  # Write encrypted file
  f = open(write_fn, 'wb')
  f.write(encrypted)
  f.close()


##
# Opens an encrypted file to decrypt using a private key stored during the
# encryption process.
#
# author: mjhwa@yahoo.com
##
def decrypt(encrypted_filename):
  # Open encrypted file
  f = open(encrypted_filename, 'rb')
  message = f.read()
  f.close()

  # Read private key
  with open(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)), 
      'private_key.pem'
    ), 
    'rb'
  ) as key_file:
    private_key = serialization.load_pem_private_key(
      key_file.read(),
      password = None,
      backend = default_backend()
    )
    key_file.close()

  # Decrypt with private key
  return private_key.decrypt(
    message,
    padding.OAEP(
      mgf = padding.MGF1(algorithm = hashes.SHA256()),
      algorithm = hashes.SHA256(),
      label = None
    )
  )


##
# Simple encryption based on a key.
#
# author: mjhwa@yahoo.com
##
def simpleEncrypt(read_fn, write_fn):
  # Check to see that the filenames are different
  if (read_fn == write_fn):
    raise Exception('Read and write filenames cannot be the same')

  # Open unencrypted file
  f = open(read_fn, 'rb')
  message = f.read()
  f.close()

  # Read key
  key_file = open(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'token_key'
    ), 'rb'
  )
  key = key_file.read()
  key_file.close()

  # Encrypt with key
  encrypted = ''.join(chr(ord(c)^ord(k)) for c,k in izip(message, cycle(key)))

  # Write encrypted file
  f = open(write_fn, 'wb')
  f.write(encrypted)
  f.close()


##
# Simple decryption based on a key.
#
# author: mjhwa@yahoo.com
##
def simpleDecrypt(read_fn):
  # Open encrypted file
  f = open(read_fn, 'rb')
  message = f.read()
  f.close()

  # Read key
  key_file = open(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'token_key'
    ), 'rb'
  )
  key = key_file.read()
  key_file.close()

  # Decrypt with key
  return ''.join(chr(ord(c)^ord(k)) for c,k in izip(message, cycle(key)))


def main():
  print('[1] encrypt')
  print('[2] decrypt')
  print('[3] simple encrypt')
  print('[4] simple decrypt')
  try:
    choice = int(raw_input('selection: '))
  except ValueError:
    return

  if choice == 1:
    read_fn = raw_input('read filename to encrypt: ')
    write_fn = raw_input('write encrypted filename: ')

    # Encrypt with public key
    encrypt(read_fn, write_fn)
  elif choice == 2:
    filename = raw_input('decrypt filename: ')

    # Decrypt with private key
    print(decrypt(filename))
  elif choice == 3:
    read_fn = raw_input('read filename to encrypt: ')
    write_fn = raw_input('write encrypted filename: ')
 
    # Encrypt with simple key
    simpleEncrypt(read_fn, write_fn)
  elif choice == 4:
    filename = raw_input('decrypt filename: ')

    # Decrypt with simple key
    print(simpleDecrypt(filename))

if __name__ == "__main__":
  main()
