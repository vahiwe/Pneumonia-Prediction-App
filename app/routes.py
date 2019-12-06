from app import app, db, mail
from flask import render_template, flash, redirect, url_for, request, jsonify, session
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message
from app.models import User, History
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from app.forms import EditProfileForm, UploadForm, PasswordChangeForm, EmailForm, PasswordForm
from PIL import Image
from threading import Thread
import time
from itsdangerous import URLSafeTimedSerializer
import hashlib
import datetime as dater
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
from sqlalchemy.exc import IntegrityError
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
        send_confirmation_email(user.email)
        flash('Congratulations, you are now a registered user!')
        flash('Thanks for registering!  Please check your email to confirm your email address.', 'success')
        return redirect(url_for('login'))
    return render_template('signUp.html', title='Register', form=form)

@app.route('/reset', methods=["GET", "POST"])
def reset():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = EmailForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first_or_404()
        except:
            flash('Invalid email address!', 'error')
            return render_template('password_reset_email.html', form=form)
         
        if user.email_confirmed:
            send_password_reset_email(user.email)
            flash('Please check your email for a password reset link.', 'success')
        else:
            flash('Your email address must be confirmed before attempting a password reset.', 'error')
        return redirect(url_for('login'))
    return render_template('password_reset_email.html', form=form)


@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    form = PasswordForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=email).first_or_404()
        except:
            flash('Invalid email address!', 'error')
            return redirect(url_for('login'))

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password_with_token.html', form=form, token=token)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
    except:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('login'))
 
    user = User.query.filter_by(email=email).first()
 
    if user.email_confirmed:
        if current_user.is_authenticated:
            flash('Account already confirmed.', 'info')
        else:
            flash('Account already confirmed. Please login.', 'info')
            return redirect(url_for('login'))
    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        flash('Thank you for confirming your email address!')
 
    return redirect(url_for('dashboard'))

@app.route('/resend_confirmation')
@login_required
def resend_email_confirmation():
    if current_user.email_confirmed:
        flash('Email is already confirmed.')
        return redirect(url_for('edit_profile'))

    try:
        send_confirmation_email(current_user.email)
        flash('Email sent to confirm your email address.  Please check your email!', 'success')
    except IntegrityError:
        flash('Error!  Unable to send email to confirm your email address.', 'error')
 
    return redirect(url_for('edit_profile'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            current_user.set_password(form.password2.data)
            flash('Your password has been changed.')
            db.session.commit()
        else:
            flash('Your password is still the same.')
        return redirect(url_for('change_password'))
    if current_user.photo == None:
        return render_template('password_change.html', form=form)
    file_url = photos.url(current_user.photo)
    return render_template('password_change.html', form=form, file_url=file_url)


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
        today = dater.date.today()
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


def send_async_email(msg):
    with app.app_context():
        mail.send(msg)
 
 
def send_email(subject, recipients, text_body, html_body):
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()


def send_confirmation_email(user_email):
    confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    confirm_url = url_for('confirm_email',token=confirm_serializer.dumps(user_email, salt='email-confirmation-salt'),_external=True)

    html = render_template('email_confirmation.html',confirm_url=confirm_url)

    send_email('Confirm Your Email Address', [user_email], html, html)


def send_password_reset_email(user_email):
    password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    password_reset_url = url_for('reset_with_token',token=password_reset_serializer.dumps(user_email, salt='password-reset-salt'),_external=True)

    html = render_template('email_password_reset.html',password_reset_url=password_reset_url)

    send_email('Password Reset Requested', [user_email], html, html)
