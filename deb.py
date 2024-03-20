import datetime
import json
import base64
import io
# from io import BytesIO
import cv2 as cv
import numpy as np
import bcrypt
import pymysql
import psycopg2
import pymysql.cursors
import jwt
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response

app = Flask(__name__)
app.secret_key = "this_is_worlds_most_secured_secret_key"
# mydb = pymysql.connect(
#     host = "localhost",
#     user = "root",
#     password = "Vedp9565@",
#     database = "media_database"
# )
mydb=psycopg2.connect("postgresql://ved:_fH3BfLkIHVWrNGQkG557Q@papamerepapa-9041.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/pRock?sslmode=verify-full")
cur = mydb.cursor()
# cur.execute("use pRock")
# if mydb.open:
#     print("Connected")
#     cur = mydb.cursor()
#     cur.execute("use media_database")
# else:
#     print("Falied to connect")
salt = bcrypt.gensalt()
def hash_password(password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def blob_to_base64(blob_data):
    return base64.b64encode(blob_data).decode('utf-8')

def base64_to_blob(base64_string):
    decoded_bytes = base64.b64decode(base64_string)
    # blob = io.BytesIO(decoded_bytes)
    return decoded_bytes

def resize(blob_data):
    new_width = 800
    new_height = 600
    # img_obj = io.BytesIO(blob_data)
    # with Image.open(img_obj) as img:
    #     print(img.size)
    #     # resized_img = img.resize((new_width, new_height))
    #     # print(resized_img.size)
    #     return np.array(img)
    img_array = np.frombuffer(blob_data, dtype=np.uint8)
    # img_cv = cv.imdecode(img_array, flags=cv.IMREAD_COLOR)
    # if img_array == None:
    #     print("wtf")
    print(img_array)
    toBeReturned = img_array
    # toBeReturned = np.array(toBeReturned)
    print(toBeReturned.size)
    return toBeReturned
    # base64_string = base64.b64encode(blob_data).decode('utf-8')
    # blob_bytes = base64.b64decode(base64_string)
    # nparr = np.frombuffer(blob_data, np.uint8)
    # image = cv.imdecode(nparr, cv.IMREAD_COLOR)
    # print("image: ", image)
    # # print(blob_data)
    # resized_image = cv.resize(image, (new_width, new_height))
    # return resized_image.tostring()

not_allowed = 0

@app.route('/', methods=['POST','GET'])
def index():
    return render_template("home.html")

@app.route('/phin', methods=['POST', 'GET'])
def phin():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    return render_template("index.html")

@app.route('/video', methods=['POST', 'GET'])
def video():
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    # print("entered")
    files = request.files.getlist('image')
    # print("number: ", files)
    uname = session['user_details']['username']
    # print(uname)
    # query = 'SELECT id FROM users WHERE username = %s'
    # cur.execute(query, uname)
    query = 'SELECT id FROM users WHERE username = $1'
    cur.execute(query, (uname,))

    fId = cur.fetchone()
    # print("fid: ", fId)
    if fId:
        for img in files:
            print(img)
            filename = img.filename
            # with open(f"{filename}", 'rb') as img:
            fileblob = img.read()
            filesize = len(fileblob)
            fidin = int(fId[0])
            # print("file size: ", filesize)
            print("Bin data: ", fileblob)
            if filesize != 0:
                query = f'INSERT INTO uploaded_images (user_id, image_name, fsize, bindata) VALUES ({fidin}, "{filename}", {filesize}, %s)'
                cur.execute(query, (fileblob))
                mydb.commit()
                print(fId, filename)
    return redirect(url_for('newHome'))

@app.route('/next/<typer>', methods=['POST', 'GET'])
def add(typer):
    token = session.get('jwt_token')
    if token:
        return redirect(url_for('newHome'))
    query = 'select username, email, password from users'
    cur.execute(query)
    list_of_users = cur.fetchall()
    if request.method == 'POST' and typer == 'signin':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password = hash_password(password)
        if name == 'Admin':
            return render_template("login.html", err="Please choose a different username", new=typer)
        if email == 'admin@iiit.ac.in':
            return render_template("login.html", err="Please choose a different email", new=typer)
        user_data = {
            "name": name,
            "email": email,
            "password": password
        }
        for items in list_of_users:
            if items[0] == name or items[1] == email:
                return render_template("login.html", err="User already exists", new=typer)
        query = f'insert into users (username, email, password) values ("{name}", "{email}", "{password}")'
        secret_key = '!@#$%'
        payload = {
            # 'user_id': 1,
            'username': name,
            'password': password,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expiration time
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        session['jwt_token'] = token
        session['user_details'] = {'username': name}
        cmd = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        cur.execute(cmd, (name, email, password))
        mydb.commit()
        return redirect(url_for('newHome'))
    elif request.method == 'POST' and typer == 'login':
        # name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        query = 'SELECT username FROM users WHERE email = $1'
        cur.execute(query, (email,))

        name = cur.fetchone()
        if name == None:
            return render_template("login.html", err="User not found", new=typer)
        # print("name :", name[0])
        user_data = {
            "email": email,
            "password": password
        }
        # for items in list_of_users:
        #     if items[1] == email:
        #         temp = items[2]
        #         if bcrypt.checkpw(password.encode('utf-8'), temp.encode('utf-8')):
                    
        # with open('users.txt', 'r') as file:
        for items in list_of_users:
            if items[1] == email:
                temp = items[2]
                if bcrypt.checkpw(password.encode('utf-8'), temp.encode('utf-8')):
                    secret_key = '!@#$%'
                    payload = {
                        # 'user_id': 1,
                        'username': name[0],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expiration time
                    }
                    token = jwt.encode(payload, secret_key, algorithm='HS256')
                    session['jwt_token'] = token
                    session['user_details'] = {'username': name[0]}
                    # print(session)
                    return redirect(url_for('newHome'))
        return render_template("login.html", err="Incorrect username / password", new=typer)
    return render_template("login.html", new=typer)

@app.route('/home2', methods=['POST', 'GET'])
def newHome():
    global not_allowed
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    uname = session['user_details']['username']
    if not_allowed == 1:
        not_allowed = 0
        return render_template('home2.html', user=uname, permission="Sorry! you don't have access to this feature")
    return render_template('home2.html', user=uname, permission="")

@app.route('/newVideo', methods = ['GET', 'POST'])
def displays():
    return render_template('video.html')

@app.route('/users', methods = ['POST', 'GET'])
def display():
    global not_allowed
    token = session.get('jwt_token')
    if not token:
        return redirect(url_for('index'))
    uname = session['user_details']['username']
    if uname != 'Admin':
        not_allowed = 1
        return redirect(url_for('newHome'))
    query = 'select username, email, password from users'
    cur.execute(query)
    list_of_users = cur.fetchall()
    print(list_of_users)
    return jsonify(list_of_users)

@app.route('/create', methods=['GET', 'POST'])
def crVid():
    img_blobs = []
    unique_uname = session['user_details']['username']
    # print(unique_uname)
    query = 'SELECT id FROM users WHERE username = $1'
    cur.execute(query, (unique_uname,))
    print(query)

    uId = cur.fetchone()
    uId = uId[0]
    # print(uId)
    # query = f'select bindata from uploaded_images where user_id = {uId}'
    # cur.execute(query)
    query = 'SELECT bindata FROM upload_images WHERE user_id = $1'
    cur.execute(query, (uId,))

    lists = cur.fetchall()
    query = f'select image_name from uploaded_images where user_id = {uId}'
    cur.execute(query)
    query = 'SELECT image_name FROM upload_images WHERE user_id = $1'
    cur.execute(query, (uId,))
    names = cur.fetchall()
    actual_names = []
    for fileName in names:
        actual_names.append(fileName[0])
    
    # print(lists)
    nice_images  =[]
    for items in lists:
        img_blobs.append(items[0])
    if len(img_blobs) == 0:
        uname = session['user_details']['username']
        return render_template('home2.html', user=uname, permission="No images are selected")
    for blobs in img_blobs:
        nice_images.append(blob_to_base64(blobs))
    # print(nice_images)
    return render_template('select.html', nice_images=nice_images, searchList=actual_names)

@app.route('/slideshow', methods = ['GET', 'POST'])
def show():
    fetched_data = request.form.getlist('images')
    # print(fetched_data)
    bg_music = request.form.get('bgm')
    print(bg_music)
    audio_flag = request.form.get('music_flag')
    print(audio_flag)
    blobs = []
    for imgs in fetched_data:
        blobs.append(base64_to_blob(imgs))
    # print(blobs)
    print("before")
    resized_nps = []
    for blob in blobs:
        resized_nps.append(resize(blob))
    print(resized_nps)
    query = f'select bindata from audio_library where audio_name = "{bg_music}"'
    cur.execute(query)
    music_blob = cur.fetchone()
    music_blob = music_blob[0]
    # print(music_blob)
    return Response("success", 200)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('jwt_token', None)
    session.pop('user_details', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)

mydb.commit()
cur.close()
mydb.close()