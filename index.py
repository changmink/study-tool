
from io import BytesIO
from datetime import datetime

from flask import Flask,request
import api

app = Flask(__name__)
LAST_POINTER = "시트1!B1"

@app.route('/sheet')
def sheet():
  name = request.args.get('name')
  if name is None:
    name = "study"
  creds = api.get_creds()
  sheet_id = api.create_sheet(creds, name)
  api.write_sheet(creds, sheet_id, "시트1!A1", [["test"]])
  api.write_sheet(creds, sheet_id, LAST_POINTER, [[2]])
  return sheet_id

@app.route('/note', methods=['POST'])
def upload_note():
    time = datetime.now()
        
    sheet_id = request.form["sheet_id"]
    name = request.form["name"]
    content = request.form["content"]

    creds = api.get_creds()

    image = request.files.get("image")
    if image is not None:
        buffered_memory = BytesIO()
        image.save(buffered_memory)
        file_id = api.upload_image(creds, image)

    last_point = api.get_last_pointer(sheet_id)[0][0]
    api.write_sheet(creds, sheet_id, f'시트1!A{last_point}', [[time.strftime('%Y-%m-%d-%H:%M:%S'), name, content]])
    last_point = int(last_point) + 1
    api.set_last_pointer(sheet_id, last_point)
    return "Success"

if __name__ == "__main__":
    app.run()