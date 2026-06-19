package main

import (
	"fmt"
	"os"

	"github.com/themonomers/tesla/go/common"
	"github.com/themonomers/tesla/go/energy"
	"github.com/themonomers/tesla/go/vehicle"
)

func main() {
	// Initialize the logger to write to app.log at the Info level
	cleanup, err := common.InitLogger()
	if err != nil {
		panic(err)
	}
	defer cleanup() // Ensures files close cleanly on shutdown

	// Load global configuration and token values
	common.LoadConfig()
	common.LoadTokenConfig()

	if len(os.Args) > 1 {
		switch os.Args[1] {
		// vehicle
		case "-vehiclem3":
			fmt.Println(vehicle.Vehicle(common.EncryptedCfg.Vehicle.M3Vin))
		case "-vehiclemx":
			fmt.Println(vehicle.Vehicle(common.EncryptedCfg.Vehicle.MxVin))
		case "-notify":
			vehicle.NotifyIsTeslaPluggedIn()
		case "-earliest":
			vehicle.ChargeEarliest()
		case "-writevehicletelemetry":
			vehicle.WriteVehicleTelemetry()
		case "-startm3precondition":
			vehicle.StartM3Precondition()
		case "-startmxprecondition":
			vehicle.StartMXPrecondition()
		case "-stopm3precondition":
			vehicle.StopPreconditionCheck(common.EncryptedCfg.Vehicle.M3Vin)
		case "-stopmxprecondition":
			vehicle.StopPreconditionCheck(common.EncryptedCfg.Vehicle.MxVin)
		case "-checkm3charge":
			vehicle.CheckCharge(common.EncryptedCfg.Vehicle.M3Vin)
		case "-checkmxcharge":
			vehicle.CheckCharge(common.EncryptedCfg.Vehicle.MxVin)
		case "-schedulem3update":
			vehicle.ScheduleUpdate(common.EncryptedCfg.Vehicle.M3Vin, common.GetTomorrowTime("2:30"))
		case "-schedulemxupdate":
			vehicle.ScheduleUpdate(common.EncryptedCfg.Vehicle.MxVin, common.GetTomorrowTime("1:30"))
		case "-schedulem3softwareupdate":
			vehicle.ScheduleSoftwareUpdate(common.EncryptedCfg.Vehicle.M3Vin, 0)
		case "-schedulemxsoftwareupdate":
			vehicle.ScheduleSoftwareUpdate(common.EncryptedCfg.Vehicle.MxVin, 0)
		case "-removeteslacron":
			vehicle.RemoveTeslaCron()
		// energy
		case "-writelivesitetelemetry":
			energy.WriteLiveSiteTelemetry()
		case "-writeenergytelemetry":
			energy.WriteEnergyTelemetry()
		case "-setenergymodebasedonweather":
			energy.SetEnergyModeBasedOnWeather()
		case "-importenergydetailtodb":
			energy.ImportEnergyDetailToDB()
		case "-importenergysummarytodb":
			energy.ImportEnergySummaryToDB()
		case "-importenergytousummarytodb":
			energy.ImportEnergyTOUSummaryToDB()
		case "-importenergydatatogsheet":
			energy.ImportEnergyDataToGsheet()
		case "-importbatterychargetodb":
			energy.ImportBatteryChargeToDB()
		case "-importoutagetodb":
			energy.ImportOutageToDB()
		// maintenance
		case "-truncateemail":
			common.TruncateEmail()
		case "-gsheettoken":
			fmt.Println(common.FindOpenRow(common.EncryptedCfg.Google.EvSpreadsheetId, "Telemetry!A:A"))
		default:
			printUsage()
		}
	} else {
		printUsage()
	}
}

func printUsage() {
	fmt.Println("Usage:  ")
	fmt.Println("\n## Vehicle ##") // vehicle
	fmt.Println("-vehiclem3")
	fmt.Println("-vehiclemx")
	fmt.Println("-notify")
	fmt.Println("-earliest")
	fmt.Println("-writevehicletelemetry")
	fmt.Println("-startm3precondition")
	fmt.Println("-startmxprecondition")
	fmt.Println("-stopm3precondition")
	fmt.Println("-stopmxprecondition")
	fmt.Println("-checkm3charge")
	fmt.Println("-checkmxcharge")
	fmt.Println("-schedulem3update")
	fmt.Println("-schedulemxupdate")
	fmt.Println("-schedulem3softwareupdate")
	fmt.Println("-schedulemxsoftwareupdate")
	fmt.Println("-removeteslacron")
	fmt.Println("\n## Energy ##") // energy
	fmt.Println("-writelivesitetelemetry")
	fmt.Println("-writeenergytelemetry")
	fmt.Println("-setenergymodebasedonweather")
	fmt.Println("-importenergydetailtodb")
	fmt.Println("-importenergysummarytodb")
	fmt.Println("-importenergytousummarytodb")
	fmt.Println("-importenergydatatogsheet")
	fmt.Println("-importbatterychargetodb")
	fmt.Println("-importoutagetodb")
	fmt.Println("\n## Maintenance ##") // maintenance
	fmt.Println("-truncateemail")
}
