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

	if len(os.Args) > 1 {
		switch os.Args[1] {
		// vehicle
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
			vehicle.StopPreconditionCheck(vehicle.M3_VIN)
		case "-stopmxprecondition":
			vehicle.StopPreconditionCheck(vehicle.MX_VIN)
		case "-checkm3charge":
			vehicle.CheckCharge(vehicle.M3_VIN)
		case "-checkmxcharge":
			vehicle.CheckCharge(vehicle.MX_VIN)
		case "-schedulem3update":
			vehicle.ScheduleUpdate(vehicle.M3_VIN, common.GetTomorrowTime("2:30"))
		case "-schedulemxupdate":
			vehicle.ScheduleUpdate(vehicle.MX_VIN, common.GetTomorrowTime("1:30"))
		case "-schedulem3softwareupdate":
			vehicle.ScheduleSoftwareUpdate(vehicle.M3_VIN, 0)
		case "-schedulemxsoftwareupdate":
			vehicle.ScheduleSoftwareUpdate(vehicle.MX_VIN, 0)
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
		/*
			case "-truncatelog":
				common.TruncateLog()
		*/
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
	fmt.Println("-truncatelog")
}
