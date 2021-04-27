import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

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
    key_size = 9000,
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
    os.path.dirname(os.path.abspath(__file__))
    + '/private_key.pem', 
    'wb'
  ) as f:
    f.write(pem)

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
    os.path.dirname(os.path.abspath(__file__))
    + '/private_key.pem', 'rb'
  ) as key_file:
    private_key = serialization.load_pem_private_key(
      key_file.read(),
      password = None,
      backend = default_backend()
    )

  # Decrypt with private key
  return private_key.decrypt(
    message,
    padding.OAEP(
      mgf = padding.MGF1(algorithm = hashes.SHA256()),
      algorithm = hashes.SHA256(),
      label = None
    )
  )


def main():
  print('[1] encrypt')
  print('[2] decrypt')
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

if __name__ == "__main__":
  main()
