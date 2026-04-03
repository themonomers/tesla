package vehicle

import (
	"github.com/themonomers/tesla/go/common"
)

func init() {
	var err error

	var c = common.GetConfig()
	M3_VIN, err = c.String("vehicle.m3_vin")
	common.LogError("init(): load m3 vin", err)

	MX_VIN, err = c.String("vehicle.mx_vin")
	common.LogError("init(): load mx vin", err)
}

// Additional scheduled charging check run on crontab.  If it failed to start, this
// will attempt to start it at the target time.
func ChargeCheckM3() {
	data := GetVehicleData(M3_VIN)

	if common.IsVehicleAtPrimary(data) &&
		data["response"].(map[string]any)["charge_state"].(map[string]any)["charging_state"].(string) != "Charging" {
		common.LogMessage("chargeCheckM3(): Scheduled charging failed to start.  Starting backup charging.")
		StartChargeVehicle(M3_VIN)
	}
}

func ChargeCheckMX() {
	data := GetVehicleData(MX_VIN)

	if common.IsVehicleAtPrimary(data) &&
		data["response"].(map[string]any)["charge_state"].(map[string]any)["charging_state"].(string) != "Charging" {
		common.LogMessage("chargeCheckMX(): Scheduled charging failed to start.  Starting backup charging.")
		StartChargeVehicle(MX_VIN)
	}
}
