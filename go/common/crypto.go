package common

import (
	"errors"
	"fmt"
	"io"
	"os"

	"golang.org/x/crypto/nacl/secretbox"
)

// Reads a raw binary key from a file and forces it into a fixed 32-byte array
func GetKey(filename string) ([32]byte, error) {
	var key [32]byte

	// Open the file safely
	file, err := os.Open(filename)
	if err != nil {
		return key, fmt.Errorf("failed to open key file: %w", err)
	}
	defer file.Close()

	// Read exactly 32 bytes from the file
	// Using io.ReadFull ensures we don't accidentally read a partial key
	_, err = io.ReadFull(file, key[:])
	if err != nil {
		if errors.Is(err, io.ErrUnexpectedEOF) || errors.Is(err, io.EOF) {
			return key, errors.New("invalid key file: must be exactly 32 bytes")
		}
		return key, fmt.Errorf("failed to read key file: %w", err)
	}

	return key, nil
}

// DecryptPyNaCl takes the raw encrypted bytes from Python and the 32-byte shared key
func DecryptPyNaCl(encryptedBytes []byte, sharedKey [32]byte) ([]byte, error) {
	// 1. PyNaCl requires a 24-byte nonce prepended to the payload
	if len(encryptedBytes) < 24 {
		return nil, errors.New("ciphertext too short (missing nonce)")
	}

	// 2. Extract the nonce from the first 24 bytes
	var nonce [24]byte
	copy(nonce[:], encryptedBytes[:24])

	// 3. Extract the actual ciphertext (which includes the 16-byte authentication tag at the end)
	actualCiphertext := encryptedBytes[24:]

	// 4. Decrypt using NaCl secretbox. Open appends the decrypted plaintext
	// to the first argument (out), so we pass nil to allocate a new slice.
	plaintext, success := secretbox.Open(nil, actualCiphertext, &nonce, &sharedKey)
	if !success {
		return nil, errors.New("decryption failed: invalid key, tampered data, or bad nonce")
	}

	return plaintext, nil
}

// Decryption based on libsodium library using standard ChaCha20-Poly1305 symmetric encryption
func Decrypt(read_fn string) []byte {
	sharedKey, err := GetKey(GetFilePath(Cfg.File.PyNaClKey))
	if err != nil {
		fmt.Printf("Key Management Error: %v\n", err)
		os.Exit(1)
	}

	// 2. Open encrypted file
	message, err := os.ReadFile(read_fn)

	// 3. Decrypt the payload
	plaintext, err := DecryptPyNaCl(message, sharedKey)
	if err != nil {
		fmt.Printf("Decryption Error: %v\n", err)
		os.Exit(1)
	}

	return plaintext
}
