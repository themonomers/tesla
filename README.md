As of June 12, 2026 the Owner API is fully deprecated.   You can only use the [Tesla Fleet API](https://developer.tesla.com/docs/fleet-api/getting-started/what-is-fleet-api) to get data and the [Tesla Vehicle Command](https://github.com/teslamotors/vehicle-command) to send commands/get data.  

Registering to use the Fleet API is quick and you just need to clone the Vehicle Command repository and send commands to your localhost running [tesla-http-proxy](https://github.com/teslamotors/vehicle-command/tree/main/cmd/tesla-http-proxy).

Before running the tesla-http-proxy, you need to follow [instructions](https://github.com/teslamotors/vehicle-command/blob/main/cmd/tesla-control/README.md) to generate a private key in your system keyring and save the public key to a file.  Then you need to pair your public key with your Tesla by getting in your car, enabling bluetooth on your device running these Tesla command-line tools, and using your NFC card.  It seems you only need to generate the private and public key once.  Any Tesla vehicle you have can be paired with that same public key.  On some of the vehicle models, there's no visualization on screen informing you to tap your NFC card which can be confusing.


### /python

Track Tesla Vehicle data in Google Sheets ([example](https://docs.google.com/spreadsheets/d/1662a1ma0Z2cdnkKvn2JWClFGsu-T-QS6NNCyyuyEweA/edit?usp=sharing)), send email reminders to plug in car, calculate charging start times, and advanced schedule based preconditioning.  Additional code for Tesla Energy products that writes data to InfluxDB. 
```
src/

└── common/
    ├── argutil.py - Tools for command line arguments
    ├── configutil.py - Retrieves configuration values
    ├── cronutil.py - Crontab tools and retrieving configured cron job commands
    ├── crypto.py - Encryption and decryption functions for sensitive files
    ├── emailutil.py - Service to send and truncate emails
    ├── fileutil.py - Retrieves filepaths for configurations and secrets
    ├── googleutil.py - API calls for Google services and utilities
    ├── influxdb.py - Access to InfluxDB
    ├── logutil.py - Central logging service 
    ├── tokenutil.py - API call for the Tesla authentication flow to retrieve new access and refresh tokens, check expiration and refresh if needed
    └── utilities.py - Commonly used and helpful tools

└── energy/
    ├── api.py - API calls for Tesla Energy products
    ├── localtelemetry.py - Write real time energy data using Tesla Gateway API
    ├── mode.py - Customizes energy site behavior based on weather
    └── telemetry.py - Writes energy data to store for analysis and visualization

└── vehicle/
    ├── api.py - API calls for Tesla Vehicles
    ├── charge.py - Calculates and sets charging times to complete at a departure time for 2 EV's
    ├── climate.py - Sets up crontab for starting the car HVAC based on references stored in a Google Sheet
    ├── removecron.py - Cleans up crontabs that are meant to exist for each specific day
    ├── software.py - Simulates scheduling software updates from the vehicle interface 
    └── telemetry.py - Write all vehicle data from previous day in Google Sheet
```

Packages needed for Python:
  * python3-pip
  * google-api-python-client
  * google-auth-httplib2
  * google-auth-oauthlib
  * python-crontab
  * pytz
  * influxdb

Packages needed for Tesla Vehicle Command SDK:
  * go
  * gcc-arm-linux-gnueabi

These are some older videos I created for [in-depth walk throughs](https://www.youtube.com/watch?v=l1pqhlGSuVg&list=PLgiPnlzk2O712gwiTIquUzdfVlzIMyS2M) of the functionality and code which I'll update over time.


### /golang

I've started porting over the Python code to Golang as another backup.  I haven't replicated all the Python functions but I have the majority completed.  The Golang code is still dependent on the Python ones, e.g. configurations, tokens.  Over time, I'll continue to work on the Golang version to make it stand-alone.

I'm a beginner at Golang, and coding overall, so please forgive my design of the Golang code and folder structure.