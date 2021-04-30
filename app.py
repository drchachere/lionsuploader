from flask import Flask, render_template, url_for, request, redirect
from bs4 import BeautifulSoup
from csv import DictReader
from requests_toolbelt import MultipartEncoder
# from flask_wtf import FlaskForm
# from flask_wtf.file import FileField, FileRequired, FileAllowed
import requests
import os

app = Flask(__name__)

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        
        user_name = request.form['username']
        pass_word = request.form['password']
        doc_t = request.form['doc_type']
        filePath = request.files['myfile']
        fileName = (str(filePath)).split("'")[1]
        #print(filePath)
        filePath.save(os.path.join('tBD', filePath.filename)) #tBD = to be deleted (folder)
        #print(filePath.stream)

        headers = {
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        }

        login_data = {
            "Name": user_name,
            "Password": pass_word,
            "Submit": "Login"
        }

        try:
            # Assign value to s_i (internal student id) based on fileName
            fileData = fileName.split("_")
            with open('caseloadv2.csv', 'r') as read_obj:
                caseload_dict = DictReader(read_obj)
                for student in caseload_dict:
                    firstName = student["First Name"]
                    if (student["Last Name"].lower() == fileData[1].lower()) and (firstName[0].lower() == fileName[0].lower()):
                        s_i = student['id']  
                        # print("id: ", s_i) 
            
            # Get full "search string" for document type
            with open('uploadDocsv2.csv', 'r') as read_obj:
                docType_dict = DictReader(read_obj)
                for student in docType_dict:
                    if (student["id"] == doc_t):
                        d_t = student['type'] ### document type (what will be used to search student pages)
                        # print("document type: ", d_t)

            # Login and get sessionID (for creating post urls for upload)        
            s = requests.Session()
            url = "https://osse.pcgeducation.com/easyiep.plx?op=login&CustomerName=dcelhpcs"
            r = s.post(url, data=login_data, headers=headers)
            soup = BeautifulSoup(r.content, "html.parser")
            enclosing_tag =(soup.find('frame'))
            almost_string = (str(enclosing_tag).split(" ")[-2])
            a_s = almost_string.split("=")[-1]
            sessionID = a_s.replace('"', '')
            # print("sessionID: ", sessionID)

            # Get the document id (get request to op=studentpage, then search soup)
            url = "https://osse.pcgeducation.com/easyiep.plx?op=studentpage&page=12&StudentID="+s_i+"&CustomerName=dcelhpcs&SessionID="+sessionID+"&PageLabel=Documents"
            r = s.get(url, headers=headers)
            soup = BeautifulSoup(r.content, "html.parser")
            typeTag = (soup.find('a', id=d_t))
            parentTypeTag = typeTag.parent
            docNumTag = ((parentTypeTag.previous_sibling).previous_sibling)
            docID = str(docNumTag).split('"')[-2]
            # print("docID: ", docID)

            # Post request to upload!
            m = MultipartEncoder(fields={"Submit": "Upload File", "boundary": "----WebKitFormBoundaryJgGlLbKTTu3Ly2BR", "AttachToDocument": "1", "lOperations": "UploadExternalDocument", "ExternalDocumentName": fileName, "AttachDocID": docID, "ExternalDocumentFile": (fileName, open('tBD/'+fileName, 'rb'), 'pdf')})
            #print("Got this far!")
            url = "https://osse.pcgeducation.com/easyiep.plx?op=upload_external_documents&StudentID="+s_i+"&CustomerName=dcelhpcs&SessionID="+sessionID
            #url2 = "https://httpbin.org/post"

            r = s.post(url, data=m, headers={'Content-Type': m.content_type, 'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"})
            if os.path.exists('tBD/'+fileName):
                os.remove('tBD/'+fileName)
            # print(r.status_code)
            

            return render_template("index.html")

        except:
            return "There was an issue.  Please make sure your login credentials are correct, and that the file is named correctly."
    else:
        return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)