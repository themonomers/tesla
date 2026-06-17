package common

import (
	"log/slog"

	"gopkg.in/ini.v1"
)

type AppConfig struct {
	File struct {
		Config           string `ini:"config"`
		LocalConfig      string `ini:"local_config"`
		LogConfig        string `ini:"log_config"`
		Token            string `ini:"token"`
		LocalToken       string `ini:"local_token"`
		TeslaKey         string `ini:"tesla_key"`
		TeslaCert        string `ini:"tesla_cert"`
		GoogleMailSecret string `ini:"google_mail_secret"`
		GoogleMailToken  string `ini:"google_mail_token"`
		GoogleSheetCred  string `ini:"google_sheet_cred"`
		LogFilename      string `ini:"log_filename"`
	} `ini:"file"`
	Cron struct {
		ChargeCheck               string `ini:"charge_check"`
		ClimateStart              string `ini:"climate_start"`
		ClimateStop               string `ini:"climate_stop"`
		ApiScheduleSoftwareUpdate string `ini:"api_schedule_software_update"`
		Redirect                  string `ini:"redirect"`
	} `ini:"cron"`
	Uri struct {
		TeslaBaseProxyUrl         string `ini:"tesla_base_proxy_url"`
		TeslaBaseFleetUrl         string `ini:"tesla_base_fleet_url"`
		TeslaBaseAuthUrl          string `ini:"tesla_base_auth_url"`
		TeslaUserAuthUrl          string `ini:"tesla_user_auth_url"`
		TesladeveloperRedirectUri string `ini:"tesladeveloper_redirect_uri"`
		OpenweathermapBaseUrl     string `ini:"openweathermap_base_url"`
	} `ini:"uri"`
	General struct {
		Timezone string `ini:"timezone"`
	} `ini:"general"`
}

type EncryptedAppConfig struct {
	Google struct {
		EvSpreadsheetId     string `ini:"ev_spreadsheet_id"`
		LogSpreadsheetId    string `ini:"log_spreadsheet_id"`
		TelemetrySheetId    int64  `ini:"telemetry_sheet_id"`
		LogSheetId          int64  `ini:"log_sheet_id"`
		EnergySpreadsheetId string `ini:"energy_spreadsheet_id"`
		SummarySheetId      int64  `ini:"summary_sheet_id"`
	} `ini:"google"`
	Tesla struct {
		ClientId     string `ini:"client_id"`
		ClientSecret string `ini:"client_secret"`
	} `ini:"tesla"`
	Vehicle struct {
		M3Vin        string  `ini:"m3_vin"`
		MxVin        string  `ini:"mx_vin"`
		PrimaryLat   float64 `ini:"primary_lat"`
		PrimaryLng   float64 `ini:"primary_lng"`
		SecondaryLat float64 `ini:"secondary_lat"`
		SecondaryLng float64 `ini:"secondary_lng"`
	} `ini:"vehicle"`
	Energy struct {
		SiteId    string `ini:"site_id"`
		BatteryId string `ini:"battery_id"`
	} `ini:"energy"`
	Notification struct {
		SenderEmail    string `ini:"sender_email"`
		SenderPassword string `ini:"sender_password"`
		Email1         string `ini:"email_1"`
		Email2         string `ini:"email_2"`
	} `ini:"notification"`
	Query struct {
		Query1 string `ini:"query_1"`
		Query2 string `ini:"query_2"`
		Query3 string `ini:"query_3"`
		Query4 string `ini:"query_4"`
	} `ini:"query"`
	Weather struct {
		OpenweathermapKey string `ini:"openweathermap_key"`
		Zipcode           string `ini:"zipcode"`
	} `ini:"weather"`
	Influxdb struct {
		Host     string `ini:"host"`
		Port     string `ini:"port"`
		User     string `ini:"user"`
		Password string `ini:"password"`
	} `ini:"influxdb"`
}

type LocalAppConfig struct {
	Energy struct {
		Email    string `ini:"email"`
		Password string `ini:"password"`
		BaseUrl  string `ini:"base_url"`
	} `ini:"energy"`
	General struct {
		Timezone string `ini:"timezone"`
	} `ini:"general"`
}

var Cfg *AppConfig
var EncryptedCfg *EncryptedAppConfig
var LocalCfg *LocalAppConfig

// Configuration loader
func LoadConfig() {
	// Load the raw INI file
	cfgFile, _ := ini.Load(GetFilePath("./configs/config.ini"))

	// Initialize the structural container
	Cfg = &AppConfig{}

	// Map the raw INI sections directly into the Go struct
	cfgFile.MapTo(Cfg)

	encryptedCfgFile, _ := ini.Load(Decrypt(GetFilePath(Cfg.File.Config)))
	EncryptedCfg = &EncryptedAppConfig{}
	encryptedCfgFile.MapTo(EncryptedCfg)

	localCfgFile, _ := ini.Load(Decrypt(GetFilePath(Cfg.File.LocalConfig)))
	LocalCfg = &LocalAppConfig{}
	localCfgFile.MapTo(LocalCfg)

	slog.Debug("Loading configurations complete.")
}
