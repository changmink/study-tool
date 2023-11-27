import os.path
from io import BytesIO
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from flask import Flask,request

app = Flask(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]
LAST_POINTER = "시트2!B1"

def read_sheet(creds, spreadsheet_id, range_name):
    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return

        return values
    except HttpError as err:
        print(err)

def write_sheet(creds, spreadsheet_id, range_name, values):
    try:
        service = build("sheets", "v4", credentials=creds)
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def get_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds

def create_sheet(creds, title):
  try:
    service = build("sheets", "v4", credentials=creds)
    spreadsheet = {"properties": {"title": title}}
    spreadsheet = (
        service.spreadsheets()
        .create(body=spreadsheet, fields="spreadsheetId")
        .execute()
    )
    print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
    return spreadsheet.get("spreadsheetId")
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error

@app.route('/sheet')
def sheet():
  creds = get_creds()
  sheet_id = create_sheet(creds, "study2")
  write(creds, sheet_id, "시트1!A1", [["test"]])
  return sheet_id

@app.route('/note', methods=['POST'])
def upload_note():
    time = datetime.now()
        
    sheet_id = request.form["sheet_id"]
    name = request.form["name"]
    content = request.form["content"]

    creds = get_creds()

    image = request.files.get("image")
    if image is not None:
        buffered_memory = BytesIO()
        image.save(buffered_memory)
        try:
            # create drive api client
            service = build("drive", "v3", credentials=creds)

            file_metadata = {
                "name": "1.jpeg",
            }
            media = MediaIoBaseUpload(image, mimetype=image.mimetype, resumable=True)
            # pylint: disable=maybe-no-member
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id, name, mimeType, webViewLink, exportLinks")
                .execute()
            )
            print(f'File with ID: "{file.get("id")}" has been uploaded.')

        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

    last_point = get_last_pointer(sheet_id)[0][0]
    write_sheet(creds, sheet_id, f'시트1!A{last_point}', [[time.strftime('%Y-%m-%d-%H:%M:%S'), name, content]])
    last_point = int(last_point) + 1
    set_last_pointer(sheet_id, last_point)
    return "Success"


def set_last_pointer(sheet_id, pointer):
    creds = get_creds()
    write_sheet(creds, sheet_id, LAST_POINTER, [[pointer]])

def get_last_pointer(sheet_id):
    creds = get_creds()
    values = read_sheet(creds, sheet_id, LAST_POINTER)
    print(type(values))
    return values

if __name__ == "__main__":
    app.run()