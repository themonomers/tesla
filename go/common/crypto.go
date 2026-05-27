package common

import (
	"os"
)

// Simple decryption based on a key.
func Decrypt(read_fn string) []byte {
	// open encrypted file
	message, _ := os.ReadFile(read_fn)

	// read key
	key, _ := os.ReadFile(GetFilePath(GetFiles().Secrets.TeslaKey))

	// decrypt with key
	result := []byte{}
	keyIndex := 0
	for _, c := range message {
		result = append(result, byte(c)^byte(key[keyIndex]))
		keyIndex = (keyIndex + 1) % len(key)
	}

	return result
}
