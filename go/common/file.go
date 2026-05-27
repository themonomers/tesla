package common

import (
	"encoding/json"
	"log/slog"
	"os"
	"path/filepath"
	"strings"
)

type Configs struct {
	Config      string `json:"config"`
	LocalConfig string `json:"localConfig"`
	Cron        string `json:"cron"`
	Log         string `json:"log"`
}

type Secrets struct {
	Token            string `json:"token"`
	LocalToken       string `json:"localToken"`
	TeslaKey         string `json:"teslaKey"`
	TeslaCert        string `json:"teslaCert"`
	GoogleMailSecret string `json:"googleMailSecret"`
	GoogleMailToken  string `json:"googleMailToken"`
	GoogleSheetCred  string `json:"googleSheetCred"`
}

type Logs struct {
	Filename string `json:"filename"`
}

type Files struct {
	Configs Configs `json:"configs"`
	Secrets Secrets `json:"secrets"`
	Logs    Logs    `json:"logs"`
}

func GetFiles() Files {
	// Read the entire file into a byte slice
	fileBytes, err := os.ReadFile("/home/pi/tesla/python/configs/file.json")
	if err != nil {
		slog.Error("GetFiles(): os.ReadFile(): " + err.Error())
	}

	// Initialize the target variable
	var files Files

	// Parse the raw bytes into the struct address
	err = json.Unmarshal(fileBytes, &files)
	if err != nil {
		slog.Error("GetFiles(): json.Unmarshal(): " + err.Error())
	}

	return files
}

func GetFilePath(file string) string {
	cwd, _ := os.Getwd()
	parent := filepath.Dir(cwd)

	return parent + "/python" + strings.TrimPrefix(file, ".")
}
