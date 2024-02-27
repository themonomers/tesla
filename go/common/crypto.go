package common

import (
	"os"
)

// Simple decryption based on a key.
func Decrypt(read_fn string) []byte {
	// open encrypted file
	message, err := os.ReadFile(read_fn)
	LogError("Decrypt(): os.ReadFile encrypted file", err)

	// read key
	key, err := os.ReadFile("/home/pi/tesla/python/tesla_private_key.pem")
	LogError("Decrypt(): os.ReadFile key", err)

	// decrypt with key
	result := []byte{}
	keyIndex := 0
	for _, c := range message {
		result = append(result, byte(c)^byte(key[keyIndex]))
		keyIndex = (keyIndex + 1) % len(key)
	}

	return result
}
