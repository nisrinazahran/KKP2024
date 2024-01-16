from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file, make_response
from pymongo import MongoClient
import jwt
import datetime
from datetime import datetime, timedelta
import hashlib
from werkzeug.utils import secure_filename
from bson import ObjectId
import pdfcrowd
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DBNAME")
SECRET_KEY = os.environ.get("SECRET_KEY")
algorithms = os.environ.get("algorithms")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

ALGO = algorithms
SECRET_KEY = SECRET_KEY

TOKEN_KEY = 'mytoken'
TOKEN_ADMIN = 'admintoken'

@app.route('/')
def homeLogin():
    return render_template('home.html')

@app.route('/admin', methods=['GET'])
def home_admin():
    token_receive = request.cookies.get(TOKEN_ADMIN)
    data_masyarakat = db.user.find()
    data_kelahiran = list(db.kelahiran.find({}))
    for d in data_kelahiran:
        d["_id"] = str(d["_id"])

    data_kematian = list(db.kematian.find({}))
    for d in data_kematian:
        d["_id"] = str(d["_id"])

    data_domisili = list(db.domisili.find({}))
    for d in data_domisili:
        d["_id"] = str(d["_id"])

    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO,
        )
        name_info = db.admin.find_one({
            'id': payload["id"]})
        return render_template(
            'profile_admin.html', 
            name_info=name_info, 
            data_masyarakat=data_masyarakat,
            data_kelahiran = data_kelahiran,
            data_kematian = data_kematian,
            data_domisili = data_domisili)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('loginAdmin'))
    
@app.route ('/lihat_syarat/<file>', methods=['GET'])
def lihat_syarat(file):
    path= "./static/syarat/"
    file_path = os.path.join(path, file)  
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    
    else:
        return 'File not found'

@app.route('/user', methods=['GET'])
def home_user():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO,
        )
        print(payload)
        name_info = db.user.find_one({
            'name': payload["name"]})
        print(name_info)
        return render_template('user.html', name_info=name_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('loginUser'))

@app.route('/login/admin')
def loginAdmin():
    msg = request.args.get('msg')
    return render_template('login_admin.html', msg=msg)

@app.route('/login/user')
def loginUser():
    msg = request.args.get('msg')
    return render_template('login_user.html', msg=msg)

@app.route('/register/user', methods=['POST'])
def register_user():
    username_receive = request.form.get('username_give')
    longname_receive = request.form.get('longname_give')
    nik_receive = request.form.get('nik_give')
    alamat_receive = request.form.get('alamat_give')
    pw_receive = request.form.get('pw_give')
    count = db.user.count_documents({})
    num = count + 1

    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    db.user.insert_one({
        "num":num,
        "long_name" : longname_receive,
        "name": username_receive, 
        "nik": nik_receive,
        "alamat": alamat_receive,
        "pw": pw_hash,
        "profile_pic" : "",
        "profile_pic_real": "profile_pics/profile_placeholder.png"})
    return jsonify({"result": "success"})

# api login sisi admin
@app.route('/login/admin', methods=['POST'])
def login_admin():
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]

    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    result = db.admin.find_one({
        "id": id_receive,
        "pw": pw_hash
        })
    if result is not None:
        payload ={
            "id": id_receive,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(
            payload,
            SECRET_KEY,
            ALGO
            )
        return jsonify({"result": "success", "token": token})
    else:
        return jsonify({"result": "fail", "msg": "Either your Id or your password is incorrect"})
    
# api login sisi user
@app.route('/login/user', methods=['POST'])
def login_user():
    username_receive = request.form["username_give"]
    pw_receive = request.form["pw_give"]

    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    result = db.user.find_one({
        "name": username_receive, 
        "pw": pw_hash
        })
    if result is not None:
        payload ={
            "name": username_receive,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(
            payload,
            SECRET_KEY,
            ALGO
            )
        return jsonify({"result": "success", "token": token})
    else:
        return jsonify({"result": "fail", "msg": "Either your username or your password is incorrect"})

@app.route('/homepage_user/pengaduan',methods=['GET'])
def pengaduan():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO
        )
        name_info = db.user.find_one({
            'name': payload["name"]})
        return render_template('pengaduan.html', name_info=name_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('loginUser'))

@app.route('/posting',methods=['POST'])
def pengaduan_post():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, ALGO)        
        name_info = db.user.find_one({
            'name': payload["name"]})
        name = request.form.get('name')
        pengaduan = request.form.get('pengaduan')
        tanggal = request.form.get('tanggal')
        tanggal_upload = request.form['today']
        file = request.files["file"]
        
        file_path= ""
        if file:
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            today = datetime.now()
            mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
            file_path = f'pengaduan-{mytime}.{extension}'
            file.save("./static/bukti/" + file_path)

        
        doc={
            "name" : name,
            "pengaduan": pengaduan,
            "tanggal_kejadian": tanggal,
            "file":file_path,
            "tanggal_upload":tanggal_upload
        }
        print(doc)
        db.pengaduan.insert_one(doc)

        return jsonify({"result": "success"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))

@app.route ('/download_pengaduan/<file>', methods=['GET'])
def download_pengaduan(file):
    path= "./static/bukti/"
    file_path = os.path.join(path, file)  
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    
    else:
        return 'File not found'

@app.route ('/posting/pengaduan', methods=['GET'])
def pengaduan_get():
    username_receive = request.args.get('username_give')
    if username_receive == '':
        posts = list(db.pengaduan.find({}).sort('date', -1).limit(20))
    else:
        posts = list(
                db.pengaduan.find({'username': username_receive}).sort('date', -1).limit(20)
            )
    for post in posts:
        post['_id'] = str(post['_id'])
    return jsonify({
            'result': 'success', 
            'msg': 'Successful fetched all posts',
            'posts': posts})

@app.route('/homepage_user/status/<username>',methods=['GET'])
def status(username):
    token_receive = request.cookies.get(TOKEN_KEY)
    status_kelahiran = db.kelahiran.find({'username': username})
    status_domisili = db.domisili.find({'username': username})
    status_kematian = db.kematian.find({'username': username})

    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO,
        )
        status = username == payload.get('name')
        name_info = db.user.find_one({
            'name': username},
            {'_id' : False})
        return render_template(
            'status.html', 
            name_info=name_info, 
            status = status,
            status_domisili = status_domisili,
            status_kelahiran = status_kelahiran,
            status_kematian = status_kematian)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))

@app.route ('/download_surat/<file>', methods=['GET'])
def unduh_kelahiran(file):
    path= "./static/surat/"
    file_path = os.path.join(path, file)  
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    
    else:
        return 'File not found'

@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, ALGO)
        name = payload['name']
        longname_receive = request.form["longname_give"]
        
        new_doc = {
            "long_name": longname_receive,
            }
        
        if "file_give" in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{name}.{extension}"
            file.save("./static/" + file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        
        db.user.update_one(
            {"name": payload['name']}, 
            {"$set": new_doc}
            )
        return jsonify({
            'result': 'success', 
            'msg': 'Your profile has been updated'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))

@app.route('/pelayanan/kelahiran', methods=['GET'])
def kelahiran():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO,
        )
        name_info = db.user.find_one({
            'name': payload["name"]})
        return render_template('surat_kelahiran.html', name_info=name_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))

@app.route('/pelayanan/kelahiran', methods=['POST'])
def kelahiran_post():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, ALGO)        
        name = payload['name']
        
        name = request.form['name']
        tempat = request.form['tempat']
        tanggal = request.form['tanggal']
        ayah = request.form['ayah']
        ibu = request.form['ibu']
        no = request.form['no']
        jk = request.form['jenis-kelamin']
        username = request.form['username']
        count = db.kelahiran.count_documents({})
        num = count + 1

        file = request.files["pdf"]
        
        file_path= ""

        if file:
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f'Kelahiran-{name}.{extension}'
            file.save("./static/syarat/" + file_path)

        
        doc={
            "username":username,
            "num" : num,
            "nama_bayi" : name,
            "tempat_lahir": tempat,
            "tanggal_lahir": tanggal,
            "ayah":ayah,
            "ibu":ibu,
            "anak":no,
            "jk" : jk,
            "file":file_path,
            "status": "Process",
            "surat" : "",
        }
        db.kelahiran.insert_one(doc)
        return redirect('/pelayanan/kelahiran')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))

@app.route('/pelayanan/domisili', methods=['GET'])
def domisili():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO,
        )
        name_info = db.user.find_one({
            'name': payload["name"]})
        return render_template('surat_domisili.html', name_info=name_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))
    
@app.route('/pelayanan/domisili', methods=['POST'])
def domisili_post():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, ALGO)        
        name = payload['name']
        
        username = request.form['username']
        name = request.form['name']
        ttl = request.form['ttl']
        jk = request.form['jenis-kelamin']
        work = request.form['work']
        alamat = request.form['alamat']
        count = db.domisili.count_documents({})
        num = count + 1

        file = request.files["pdf"]
        
        file_path= ""

        if file:
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f'Domisili-{name}.{extension}'
            file.save("./static/syarat/" + file_path)

        
        doc={
            "username" : username,
            "num" : num,
            "nama" : name,
            "ttl" : ttl,
            "work" : work,
            "alamat":alamat,
            "jk" : jk,
            "file":file_path,
            "status": "Process",
            "surat" : "",
        }
        db.domisili.insert_one(doc)
        return redirect('/pelayanan/domisili')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))
    
@app.route('/pelayanan/kematian', methods=['GET'])
def kematian():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO,
        )
        name_info = db.user.find_one({
            'name': payload["name"]})
        return render_template('surat_kematian.html', name_info=name_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))

@app.route('/pelayanan/kematian', methods=['POST'])
def kematian_post():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, ALGO)        
        name = payload['name']
        
        username = request.form['username']
        name = request.form['nama']
        ttl = request.form['ttl']
        agama = request.form['agama']
        jk = request.form['jenis-kelamin']
        tempat = request.form['tempat']
        tanggal = request.form['tanggal']
        penyebab = request.form['penyebab']
        count = db.kematian.count_documents({})
        num = count + 1

        file = request.files["pdf"]
        
        file_path= ""

        if file:
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f'Kematian-{name}.{extension}'
            file.save("./static/syarat/" + file_path)

        
        doc={
            "username" : username,
            "num" : num,
            "nama" : name,
            "ttl" : ttl,
            "agama" :agama,
            "jk" : jk,
            "tempat" : tempat,
            "tanggal": tanggal,
            "penyebab" : penyebab,
            "file":file_path,
            "status": "Process",
            "surat" : "",
        }
        db.kematian.insert_one(doc)
        return redirect('/pelayanan/kematian')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home_user'))

@app.route('/edit/kelahiran',methods=['GET','POST'])
def edit_kelahiran():
    if request.method == "GET":
        id = request.args.get("id")
        data = db.kelahiran.find_one({"_id":ObjectId(id)})
        data["_id"]=str(data["_id"])
        print(data)
        return render_template("edit_kelahiran.html",data=data)
    
    id = request.form["id"]
    status = request.form["status"]
    file_path= ""
    file = request.files["pdf"]
    if file:
        filename = secure_filename(file.filename)
        extension = filename.split(".")[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        file_path = f'surat_kelahiran-{mytime}.{extension}'
        file.save("./static/surat/" + file_path)
    db.kelahiran.update_one({"_id":ObjectId(id)},{'$set':{"status":status,"surat":file_path}})
    return redirect('/admin')

@app.route('/edit/kematian',methods=['GET','POST'])
def edit_kematian():
    if request.method == "GET":
        id = request.args.get("id")
        data = db.kematian.find_one({"_id":ObjectId(id)})
        data["_id"]=str(data["_id"])
        print(data)
        return render_template("edit_kematian.html",data=data)
    
    id = request.form["id"]
    status = request.form["status"]
    file_path= ""
    file = request.files["pdf"]
    if file:
        filename = secure_filename(file.filename)
        extension = filename.split(".")[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        file_path = f'surat_kematian-{mytime}.{extension}'
        file.save("./static/surat/" + file_path)
    db.kematian.update_one({"_id":ObjectId(id)},{'$set':{"status":status,"surat":file_path}})
    return redirect('/admin')

@app.route('/edit/domisili',methods=['GET','POST'])
def edit_domisili():
    if request.method == "GET":
        id = request.args.get("id")
        data = db.domisili.find_one({"_id":ObjectId(id)})
        data["_id"]=str(data["_id"])
        print(data)
        return render_template("edit_domisili.html",data=data)
    
    id = request.form["id"]
    status = request.form["status"]
    file_path= ""
    file = request.files["pdf"]
    if file:
        filename = secure_filename(file.filename)
        extension = filename.split(".")[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        file_path = f'surat_domisili-{mytime}.{extension}'
        file.save("./static/surat/" + file_path)
    db.domisili.update_one({"_id":ObjectId(id)},{'$set':{"status":status,"surat":file_path}})
    return redirect('/admin')

@app.route('/convert_to_pdf/kelahiran', methods=['GET','POST'])
def convert_pdf_kelahiran():
  # Generate the HTML dynamicall
    data = {
        "nama":request.form['nama'],
        "tempat":request.form['tempat'],
        "tanggal":request.form['tanggal'],
        "gender":request.form['gender'],
        "anak":request.form['anak'],
        "ayah":request.form['ayah'],
        "ibu":request.form['ibu'],

    }
    html = render_template('resume_kelahiran.html',data=data)  # Replace 'your_template.html' with your own template

    # Create a PDFCrowd client
    client = pdfcrowd.HtmlToPdfClient('KKP2024', '840c4e11b3c775c0c7a4bbe24bcc7122')  # Replace 'username' and 'apikey' with your PDFCrowd credentials

    # Convert HTML to PDF
    pdf = client.convertString(html)

    # Create a response with the PDF content
    response = make_response(pdf)

    nama = request.form ['nama']
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Surat Kelahiran-{nama}.pdf' 
    return response

@app.route('/convert_to_pdf/kematian', methods=['GET','POST'])
def convert_pdf_kematian():
  # Generate the HTML dynamicall
    data = {
        "nama":request.form['nama'],
        "ttl":request.form['ttl'],
        "agama":request.form['agama'],
        "jk":request.form['jk'],
        "tempat":request.form['tempat'],
        "tanggal":request.form['tanggal'],
        "penyebab":request.form['penyebab'],

    }
    html = render_template('resume_kematian.html',data=data)  # Replace 'your_template.html' with your own template

    # Create a PDFCrowd client
    client = pdfcrowd.HtmlToPdfClient('KKP2024', '840c4e11b3c775c0c7a4bbe24bcc7122')  # Replace 'username' and 'apikey' with your PDFCrowd credentials

    # Convert HTML to PDF
    pdf = client.convertString(html)

    # Create a response with the PDF content
    response = make_response(pdf)

    nama = request.form ['nama']
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Surat Kematian-{nama}.pdf' 
    return response

@app.route('/convert_to_pdf/domisili', methods=['GET','POST'])
def convert_pdf_domisili():
  # Generate the HTML dynamicall
    data = {
        "nama":request.form['nama'],
        "ttl":request.form['ttl'],
        "work":request.form['work'],
        "alamat":request.form['alamat'],
        "jk":request.form['jk'],
    }
    html = render_template('resume_domisili.html',data=data)  # Replace 'your_template.html' with your own template

    # Create a PDFCrowd client
    client = pdfcrowd.HtmlToPdfClient('KKP2024', '840c4e11b3c775c0c7a4bbe24bcc7122')  # Replace 'username' and 'apikey' with your PDFCrowd credentials

    # Convert HTML to PDF
    pdf = client.convertString(html)

    # Create a response with the PDF content
    response = make_response(pdf)

    nama = request.form ['nama']
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Surat Domisili-{nama}.pdf' 
    return response


@app.route('/user/delete_birth/<birth_id>', methods=['POST'])
def delete_birth(birth_id):
    token_receive = request.cookies.get(TOKEN_KEY)
    
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO
        )
        
        # Check if the user is an admin
        if payload.get('name'):
            # Delete the user from the database
            result = db.kelahiran.delete_one({"_id": ObjectId(birth_id)})
           
            if result.deleted_count > 0:
                return jsonify({"result": "success"})
            else:
                return jsonify({"result": "fail", "msg": "failed to delete"})
        else:
            return jsonify({"result": "fail", "msg": "Unauthorized access"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({"result": "fail", "msg": "Invalid token"})

@app.route('/user/delete_domisili/<domisili_id>', methods=['POST'])
def delete_domisili(domisili_id):
    token_receive = request.cookies.get(TOKEN_KEY)
    
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO
        )
        
        # Check if the user is an admin
        if payload.get('name'):
            # Delete the user from the database
            result = db.domisili.delete_one({"_id": ObjectId(domisili_id)})
           
            if result.deleted_count > 0:
                return jsonify({"result": "success"})
            else:
                return jsonify({"result": "fail", "msg": "failed to delete"})
        else:
            return jsonify({"result": "fail", "msg": "Unauthorized access"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({"result": "fail", "msg": "Invalid token"})
    
@app.route('/user/delete_die/<die_id>', methods=['POST'])
def delete_die(die_id):
    token_receive = request.cookies.get(TOKEN_KEY)
    
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            ALGO
        )
        
        # Check if the user is an admin
        if payload.get('name'):
            # Delete the user from the database
            result = db.kematian.delete_one({"_id": ObjectId(die_id)})
           
            if result.deleted_count > 0:
                return jsonify({"result": "success"})
            else:
                return jsonify({"result": "fail", "msg": "failed to delete"})
        else:
            return jsonify({"result": "fail", "msg": "Unauthorized access"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({"result": "fail", "msg": "Invalid token"})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)