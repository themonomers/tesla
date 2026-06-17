package common

import (
	"github.com/influxdata/influxdb/client/v2"
)

func GetDBClient() client.HTTPClient {
	c, _ := client.NewHTTPClient(client.HTTPConfig{
		Addr:     "http://" + EncryptedCfg.Influxdb.Host + ":" + EncryptedCfg.Influxdb.Port,
		Username: EncryptedCfg.Influxdb.User,
		Password: EncryptedCfg.Influxdb.Password,
	})

	return c
}
