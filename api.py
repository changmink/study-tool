import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
LAST_POINTER = "시트1!G1"

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

def set_last_pointer(sheet_id, pointer):
    creds = get_creds()
    write_sheet(creds, sheet_id, LAST_POINTER, [[pointer]])

def get_last_pointer(sheet_id):
    creds = get_creds()
    values = read_sheet(creds, sheet_id, LAST_POINTER)
    print(type(values))
    return values

def upload_image(creds,image):
    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": image.filename,
        }
        media = MediaIoBaseUpload(image, mimetype=image.mimetype, resumable=True)
        # pylint: disable=maybe-no-member
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, name, mimeType, webViewLink, exportLinks")
            .execute()
        )
        print(f'File with ID: "{file.get("id")}" has been uploaded.')

        return "https://drive.google.com/file/d/" + file.get("id")
    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None
        return None