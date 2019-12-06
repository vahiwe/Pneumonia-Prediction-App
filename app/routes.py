from app import app, db
from flask import render_template, flash, redirect, url_for, request, jsonify, session
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, History
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from app.forms import EditProfileForm, UploadForm
from PIL import Image
import time
import hashlib
import datetime
import os
import urllib.request
from werkzeug.utils import secure_filename
import base64
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
import json
import numpy as np
import requests
from .preprocess import load
from flask_cors import CORS
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOADED_IMAGES_DEST'] = UPLOAD_FOLDER
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(
    os.getcwd(), 'app', 'static', 'profile')  # you'll need to create a folder named uploads

photos = UploadSet('photos', IMAGES)
images = UploadSet('images', IMAGES)
configure_uploads(app, photos)
configure_uploads(app, images)
patch_request_class(app)  # set maximum file size, default is 16MB

CORS(app)

@app.route('/test', methods=['GET', 'POST'])
def upload_fil():
    form = UploadForm()
    files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])
    return render_template('test.html', files_list=files_list, form=form)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, firstname=form.firstname.data, lastname=form.lastname.data, gender=form.gender.data, profession=form.profession.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signUp.html', title='Register', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.gender = form.gender.data
        current_user.profession = form.profession.data
        file = request.files['photo']
        if file:
            if current_user.photo != None:
                file_path = photos.path(current_user.photo)
                os.remove(file_path)
            photos.save(file)
            current_user.photo = file.filename
        if len(form.password.data) > 8 and current_user.check_password(form.password.data) and len(form.password2.data) > 8:
            current_user.set_password(form.password2.data)
            flash('Your password has been changed.')
        else:
            flash('Your password is still the same.')
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form = EditProfileForm(current_user.email)
        form.email.data = current_user.email
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.gender.data = str(current_user.gender)
        form.profession.data = str(current_user.profession)
    if current_user.photo == None:
        return render_template('settings.html', title='Edit Profile', form=form)
    file_url = photos.url(current_user.photo)
    return render_template('settings.html', title='Edit Profile', form=form, file_url=file_url)


@app.route('/history', methods=['GET'])
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    imag = History.query.filter().order_by(History.timestamp.desc()).paginate(
        page, app.config['HISTORY_PER_PAGE'], False)
    next_url = url_for('history', page=imag.next_num) \
        if imag.has_next else None
    prev_url = url_for('history', page=imag.prev_num) \
        if imag.has_prev else None
    if current_user.photo == None:
        return render_template('history.html')
    file_url = photos.url(current_user.photo)
    return render_template('history.html', file_url=file_url, imag=imag.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    form = UploadForm()
    image_count = History.query.filter().order_by(History.timestamp.desc()).count()
    if current_user.photo == None:
        return render_template('dashboard.html', form=form, image_count=image_count)
    file_url = photos.url(current_user.photo)
    return render_template('dashboard.html', form=form, file_url=file_url, image_count=image_count)

@app.route('/dashboard', methods=['POST'])
@login_required
def upload_file():
    # check if the post request has the file part
    form = UploadForm()
    if form.validate_on_submit():
        file = request.files['photo']
        ext = file.filename.rsplit('.', 1)[1]
        timestr = time.strftime("%Y%m%d-%H%M%S")
        today = datetime.date.today()
        todaystr = today.isoformat()
        nam = timestr + "." + ext
        filename = images.save(file, folder=todaystr, name=nam)
        file_url = images.url(filename)
        print(file_url)

        # Save to database
        upload = History(photo=filename, patient=form.patient.data, photo_url=file_url ,user_email=current_user.email)
        db.session.add(upload)
        db.session.commit()
        
        # Decoding and pre-processing base64 image
        img = load(file)

        # Creating payload for TensorFlow serving request
        data = json.dumps({"signature_name": "serving_default",
                    "instances": img.tolist()})
        print('Data: {} ... {}'.format(data[:50], data[len(data)-52:]))

        # Making POST request 
        # headers = {"content-type": "application/json"}
        # json_response = requests.post(
        #     'http://localhost:8501/v1/models/pneu_model:predict', data=data, headers=headers)

        # Decoding results from TensorFlow Serving server
        # predictions = json.loads(json_response.text)['predictions']
        # print(predictions)

        # Returning JSON response to the frontend
        # return jsonify(inception_v3.decode_predictions(np.array(pred['predictions']))[0])
        flash(img.shape)
        # return redirect(url_for("dashboard", extracted_text=img.shape, img_src=names))
        return redirect(url_for("dashboard"))
    if current_user.photo == None:
        return render_template('dashboard.html', form=form)
    file_url = photos.url(current_user.photo)
    image_count = History.query.filter().order_by(History.timestamp.desc()).count()
    return render_template("dashboard.html", form=form, file_url=file_url, image_count=image_count)

@app.route('/about')
def about():
    return render_template('about.html')


# route and function to handle the upload page


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
