from itertools import cycle


##
# Simple encryption of a file, based on a key.
#
# author: mjhwa@yahoo.com
##
def encryptFile(read_fn, write_fn, token_fn):
  # Check to see that the filenames are different
  if (read_fn == write_fn):
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
  if (isinstance(message, bytes) == False):
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


def main():
  print('[1] encrypt')
  print('[2] decrypt')
  try:
    choice = int(input('selection: ')) # type: ignore
  except ValueError:
    return

  if choice == 1:
    read_fn = input('read filename to encrypt: ')
    write_fn = input('write encrypted filename: ')
    token_fn = input('token filename: ')
 
    # Encrypt with simple key
    encryptFile(read_fn, write_fn, token_fn)
  elif choice == 2:
    filename = input('decrypt filename: ')
    token_fn = input('token filename: ')

    # Decrypt with simple key
    print(decrypt(filename, token_fn))

if __name__ == "__main__":
  main()
