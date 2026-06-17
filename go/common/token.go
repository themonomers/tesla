package common

import (
	"log/slog"

	"gopkg.in/ini.v1"
)

type TokenConfig struct {
	Tesla struct {
		AccessToken  string `ini:"access_token"`
		IdToken      string `ini:"id_token"`
		RefreshToken string `ini:"refresh_token"`
		CreatedAt    string `ini:"created_at"`
		ExpiresAt    string `ini:"expires_at"`
	} `ini:"tesla"`
}

type LocalTokenConfig struct {
	Tesla struct {
		Token string `ini:"token"`
	} `ini:"tesla"`
}

var TokenCfg *TokenConfig
var LocalTokenCfg *LocalTokenConfig

// Token loader
func LoadTokenConfig() {
	tokenCfgFile, _ := ini.Load(Decrypt(GetFilePath(Cfg.File.Token)))
	TokenCfg = &TokenConfig{}
	tokenCfgFile.MapTo(TokenCfg)

	localTokenCfgFile, _ := ini.Load(Decrypt(GetFilePath(Cfg.File.LocalToken)))
	LocalTokenCfg = &LocalTokenConfig{}
	localTokenCfgFile.MapTo(LocalTokenCfg)

	slog.Debug("Loading tokens complete.")
}
