
from io import BytesIO
from datetime import datetime

from flask import Flask, request, render_template
import api

app = Flask(__name__)
LAST_POINTER = "시트1!G1"

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/sheet')
def sheet():
  name = request.args.get('name')
  if name is None:
    name = "study"
  creds = api.get_creds()
  sheet_id = api.create_sheet(creds, name)
  api.write_sheet(creds, sheet_id, "시트1!A1", [["날짜", "시간", "이름", "내용", "인증"]])
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
    link = None
    if image is not None:
        buffered_memory = BytesIO()
        image.save(buffered_memory)
        link = api.upload_image(creds, image)
        

    last_point = api.get_last_pointer(sheet_id)[0][0]
    api.write_sheet(creds, sheet_id, f'시트1!A{last_point}', [[time.strftime('%Y-%m-%d'), time.strftime('%H:%M:%S'), name, content, link]])
    last_point = int(last_point) + 1
    api.set_last_pointer(sheet_id, last_point)
    return "Success"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8000')