import os

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from flask import current_app as app
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flaskr.auth import login_required
from flaskr.db import get_db
from flask import send_from_directory
#Google Maps API
from flask_googlemaps import GoogleMaps, Map
#import Geocoder
from flask_simple_geoip import SimpleGeoIP
from flaskr import simple_geoip
import json

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

bp = Blueprint('blog', __name__)

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getGeoIP():
    #retrieve geoip data for the given requester
    geoip_data = simple_geoip.get_geoip_data()
    return geoip_data

@bp.route('/<int:id>/setMap', methods=('GET', 'POST'))
@login_required
def setMap(id):
    mapList = []
    latitude = 0
    longitude = 0

    # Acquire database
    db = get_db()
    posts = db.execute(
        'SELECT p.id, username, title, imgFile, lat, lng'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE lat IS NOT NULL AND lng IS NOT NULL'
        ' ORDER BY created DESC'
    ).fetchall()

    # Parse query returns
    for row in posts:
        # Assign green markers for nearby projects
        if row[0] != id:
            marker = {'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
                      'lat': row[4],
                      'lng': row[5],
                      'infobox': "<img src='/static/myImgs/"+row[3]+"' /><br /><b>"+row[2]+"(ID: "+str(row[0])+") by "+row[1]+"</b>"}
            mapList.append(marker)
        # Assign blue marker indicating position of current project
        else:
            marker = {'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                      'lat': row[4],
                      'lng': row[5],
                      'infobox': "<b>Current Project</b>"}
            latitude = row[4]
            longitude = row[5]
            mapList.append(marker)

    mymap = Map(
        identifier = "view-side",
        style = "height:100%; width:100%; margin:0;",
        lat = latitude,
        lng = longitude,
        zoom = 15,
        markers = mapList
    )

    return render_template('blog/mymap.html', mymap=mymap)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, imgFile, wd, ht'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    imgs = db.execute(
        'SELECT image, userID, width, height'
        ' FROM album'
    ).fetchall()

    return render_template('blog/index.html', posts=posts, imgs=imgs)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    post = get_db().execute(
        'SELECT image, width, height'
        ' FROM album'
        ' WHERE userID = ?',
        (0,)
    ).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        filename = request.form['filename']
        error = ''

        #Start here
        if not title:
            error += 'Title is required.'

        if error:
            flash(error)
        else:
            #File is already saved. Add tuple to database
            db = get_db()
            if request.form['lat'] != 'none':
                db.execute(
                    'INSERT INTO post (title, body, author_id, imgFile, wd, ht, lat, lng)'
                    ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (title, body, g.user['id'], filename, request.form['width'], request.form['height'], request.form['lat'], request.form['lng'])
                    )
            else:
                db.execute(
                    'INSERT INTO post (title, body, author_id, imgFile, wd, ht)'
                    ' VALUES (?, ?, ?, ?, ?, ?)',
                    (title, body, g.user['id'], filename, request.form['width'], request.form['height'])
                    )
            db.commit()

            #Acquire latest insert id
            insertID = db.execute('SELECT last_insert_rowid()').fetchone()

            #Delete temporary tuple from album table
            db.execute('DELETE FROM album WHERE userID = 0')
            db.commit()

            #Insert new album with set ID
            db.execute(
                'INSERT INTO album (userID, image, width, height)'
                ' VALUES (?, ?, ?, ?)',
                (insertID[0], filename, request.form['width'], request.form['height'])
                )
            db.commit()

            return redirect(url_for('blog.index'))

    return render_template('blog/create.html', post=post)

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, imgFile, wd, ht'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        changeFile = False
        filename = ''
        error = ''

         # check if the post request has the file part
        if 'file' in request.files:
	        file = request.files['file']

	        # if user does not select file, browser also
	        # submit an empty part without filename
	        if file.filename:
		        if file and allowed_file(file.filename):
		            filename = secure_filename(file.filename)
		            changeFile = True

        if not title:
            error += 'Title is required.'

        if error:
            flash(error)
        else:
            db = get_db()

            # If file is real, upload and save to DB
            if changeFile:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                db.execute(
                    'UPDATE post SET title = ?, body = ?, imgFile = ?, wd = ?, ht = ?'
                    ' WHERE id = ?',
                    (title, body, filename, request.form['width'], request.form['height'], id)
                )
            else:
                db.execute(
                    'UPDATE post SET title = ?, body = ?'
                    ' WHERE id = ?',
                    (title, body, id)
                )

            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    # Acquire database
    db = get_db()
    # Delete all instances from the album
    db.execute('DELETE FROM album WHERE userID = ?', (id,))
    db.commit()
    # Delete post itself
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/imageCapture', methods=('GET', 'POST'))
@login_required
def imageCapture(id):
    # Create New Post temp ID
    post = 0
    # If updating a post
    if id != 0:
        post = get_post(id)

    if request.method == 'POST':
        filename = ''
        error = ''

        # check if the post request has the file part
        if 'file' not in request.files:
            error += 'No file part. '

         # proceed if file not empty
        if not error:
            file = request.files['file']

            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                error += 'No selected file. '

            # proceed if file is selected
            if not error:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                else:
                    error += 'File type is not allowed.'

        # If file is real, upload and save to DB
        if not error:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db = get_db()

            if id != 0:
                db.execute(
                    'UPDATE post SET imgFile = ?, wd = ?, ht = ?'
                    ' WHERE id = ?',
                    (filename, request.form['width'], request.form['height'], id)
                )
                db.commit()

                db.execute(
                    'INSERT INTO album (userID, image, width, height)'
                    ' VALUES (?, ?, ?, ?)',
                    (id, filename, request.form['width'], request.form['height'])
                )
                db.commit()
            else:
                db.execute(
                    'INSERT INTO album (userID, image, width, height)'
                    ' VALUES (?, ?, ?, ?)',
                    (id, filename, request.form['width'], request.form['height'])
                )
                db.commit()
            flash('Album Successfully Updated!')
        else:
            flash(error)

    return render_template('blog/imageCapture.html', post=post)

@bp.route('/background')
def background():
    return render_template('blog/background.html')

@bp.route('/about')
def about():
    return render_template('blog/about.html')