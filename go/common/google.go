package common

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
	"google.golang.org/api/gmail/v1"
	"google.golang.org/api/option"
	"google.golang.org/api/sheets/v4"
)

var CONFIGS map[string]string
var DELETE_THRESHOLD float64 = 30.0

func init() {
	var err error

	var c = GetConfig()
	CONFIGS, err = c.Settings() // github.com/ridgelines/go-config doesn't support loading by sections so we have to grab everything and loop
	LogError("init(): load settings", err)
}

// Looks for the next empty cell in a Google Sheet row to avoid overwriting data
// when reading/writing values.
func FindOpenRow(sheet_id, sheet_name, rng string) int {
	service := GetGoogleSheetService()
	rng = sheet_name + "!" + rng
	resp, err := service.Spreadsheets.Values.Get(sheet_id, rng).Do()
	logError("FindOpenRow(): service.Spreadsheets.Values.Get", err)

	if len(resp.Values) == 0 {
		return 1
	}

	return len(resp.Values) + 1
}

// Get Google Sheet service with edit/delete scope.
func GetGoogleSheetService() *sheets.Service {
	ctx := context.Background()
	b, err := os.ReadFile("/home/pi/tesla/go/common/google_client_secret.json")
	logError("GetGoogleSheetService(): os.ReadFile", err)

	// If modifying these scopes, delete your previously saved google_token.json.
	config, err := google.ConfigFromJSON(b, "https://www.googleapis.com/auth/spreadsheets")
	logError("GetGoogleSheetService(): google.ConfigFromJSON", err)

	client := getClient(config, "/home/pi/tesla/go/common/gsheet_token.json")

	srv, err := sheets.NewService(ctx, option.WithHTTPClient(client))
	logError("GetGoogleSheetService(): sheets.NewService", err)

	return srv
}

// Get Google Mail service with edit/delete scope.
func getGoogleMailService() *gmail.Service {
	ctx := context.Background()
	b, err := os.ReadFile("/home/pi/tesla/go/common/google_client_secret.json")
	logError("getGoogleMailService(): os.ReadFile", err)

	// If modifying these scopes, delete your previously saved google_token.json.
	config, err := google.ConfigFromJSON(b, gmail.GmailModifyScope)
	logError("GetGoogleSheetService(): google.ConfigFromJSON", err)

	client := getClient(config, "/home/pi/tesla/go/common/gmail_token.json")

	srv, err := gmail.NewService(ctx, option.WithHTTPClient(client))
	logError("getGoogleMailService(): gmail.NewService", err)

	return srv
}

// Retrieve a token, saves the token, then returns the generated client.
func getClient(config *oauth2.Config, token_filename string) *http.Client {
	// The file token_filename stores the user's access and refresh tokens, and is
	// created automatically when the authorization flow completes for the first
	// time.
	tok, err := tokenFromFile(token_filename)
	if err != nil {
		tok = getTokenFromWeb(config)
		saveToken(token_filename, tok)
	}
	return config.Client(context.Background(), tok)
}

// Request a token from the web, then returns the retrieved token.
func getTokenFromWeb(config *oauth2.Config) *oauth2.Token {
	authURL := config.AuthCodeURL("state-token", oauth2.AccessTypeOffline)
	fmt.Printf("Go to the following link in your browser then type the "+
		"authorization code: \n%v\n", authURL)

	var authCode string
	_, err := fmt.Scan(&authCode)
	logError("getTokenFromWeb(): fmt.Scan", err)

	tok, err := config.Exchange(context.TODO(), authCode)
	logError("getTokenFromWeb(): config.Exchange", err)

	return tok
}

// Retrieves a token from a local file.
func tokenFromFile(file string) (*oauth2.Token, error) {
	f, err := os.Open(file)
	logError("tokenFromFile(): os.Open", err)

	defer f.Close()
	tok := &oauth2.Token{}
	err = json.NewDecoder(f).Decode(tok)
	return tok, err
}

// Saves a token to a file path.
func saveToken(path string, token *oauth2.Token) {
	fmt.Printf("Saving credential file to: %s\n", path)
	f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	logError("saveToken(): os.OpenFile", err)

	defer f.Close()
	json.NewEncoder(f).Encode(token)
}

// Keeps the email sent folder from being overloaded with notifications; deletes
// any notification emails older than a specified number of days.
func TruncateEmail() {
	// get the date for the threshold (days prior)
	delete_date := time.Now().Add(time.Duration(-DELETE_THRESHOLD * float64(time.Hour) * 24))
	//	fmt.Println(delete_date)

	for index, element := range CONFIGS {
		if strings.Contains(index, "query.") {
			deleteEmail(element, delete_date)
		}
	}
}

func deleteEmail(query string, delete_date time.Time) {
	// Call the Gmail API and get the messages based on query
	service := getGoogleMailService()
	messages, err := service.Users.Messages.List("me").Q(query).Do()
	LogError("deleteEmail(): service.Users.Messages.List", err)

	if len(messages.Messages) == 0 {
		return
	}

	// Loop through all the messages returned
	for i := 0; i < len(messages.Messages); i++ {
		message, err := service.Users.Messages.Get("me", messages.Messages[i].Id).Do()
		LogError("deleteEmail(): service.Users.Messages.Get", err)

		email_dt := time.Unix(0, message.InternalDate*int64(time.Millisecond))
		//		fmt.Print(email_dt)
		//		fmt.Print(": ")
		//		for j := 0; j < len(message.Payload.Headers); j++ {
		//			if message.Payload.Headers[j].Name == "Subject" {
		//				fmt.Println(message.Payload.Headers[j].Value)
		//			}
		//		}

		// Check if the email date is older than the delete date threshold and
		// move to trash
		if email_dt.Before(delete_date) {
			service.Users.Messages.Trash("me", messages.Messages[i].Id).Do()
		}
	}
}
