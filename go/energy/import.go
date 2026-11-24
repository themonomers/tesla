package energy

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"time"
)

// Import missing dates for energy data into InfluxDB and Gsheet
func ImportEnergyData() {
	WriteEnergyData(getDateInput())
}

// Prompts for a date input from standard in.
func getDateInput() time.Time {
	fmt.Print("date(m/d/yyyy): ")
	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	input = strings.Replace(input, "\n", "", -1)

	date, err := time.Parse("1/2/2006", input)
	if err != nil {
		fmt.Println("Error parsing date: " + err.Error())
		os.Exit(1)
	}

	fmt.Println(date.Format("1/2/2006"))
	fmt.Print("import (y/n): ")
	input, _ = reader.ReadString('\n')
	input = strings.Replace(input, "\n", "", -1)
	if input != "y" {
		os.Exit(1)
	}

	return date
}
