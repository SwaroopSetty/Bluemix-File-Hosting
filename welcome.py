#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from flask import Flask, request, render_template
from cloudant.account import Cloudant
from cloudant.result import Result
import hashlib
import time

# Connectivity to cloudant
USERNAME = ''
PASSWORD = ''
ACCOUNT_URL = ''

client = Cloudant(USERNAME, PASSWORD, url=ACCOUNT_URL)
client.connect()
session = client.session()

# Open the database
my_database = client['files']

app = Flask(__name__)

@app.route('/')
def Welcome():
    return app.send_static_file('index.html')

################ UPLOAD LOGIC #################
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        version = 1
        file = request.files['file']
        hashcode = hashlib.md5(file.filename).hexdigest()
        content = file.read()
        
        for document in my_database:
            if document['fileName'] == file.filename:
                if document['hashValue'] == hashcode:
                    return 'File not Uploaded'
                else:
                    version = document['versionNo'] + 1

        # Create a document to be pushed cloudant
        data = {
        'id': file.filename+hashcode,
        'fileName': file.filename,
        'hashValue': hashcode,
        'versionNo':  version,
        'fileContent': content,
        'lastModifiedDate': time.ctime(os.path.getmtime(file.filename))
        }

        #Push the document to cloudant
        my_document = my_database.create_document(data)
        
        return 'File Uploaded'
        
################ FILE LIST LOGIC ################
@app.route('/list', methods=['POST', 'GET'])
def list():
    list = ''
    for document in my_database:
        list = list + document['fileName'] + '_' + str(document['versionNo'])
        list = list + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href='download?id="+document['_id']+"'>Download</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        list = list + "<a href='delete?id="+document['_id']+"'>Delete</a><br>"
    return '''<!DOCTYPE html>
<html>

  <head>
    <title>Python Flask Application</title>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="static/stylesheets/style.css">
  </head>

  <body>
    ''' + list + '''   
  </body>

</html>'''

################ DOWNLOAD LOGIC #################
@app.route('/download', methods=['POST', 'GET'])
def download():
    docID = request.args.get('id')
    document = my_database[docID]
    fname = document['fileName'] + '_' + str(document['versionNo'])
    downloadFile = open(fname,'w')
    downloadFile.write(document['fileContent'])
    return 'File Download Successful'

################ DELETE LOGIC #################
@app.route('/delete', methods=['POST', 'GET'])
def delete():
    docID = request.args.get('id')
    document = my_database[docID]
    document.delete()
    return 'File Delete Successful'


port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)
