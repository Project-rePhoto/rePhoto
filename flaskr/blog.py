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
from datetime import datetime
import shutil
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
def setMap(id):
    mapList = []
    latitude = 0
    longitude = 0

    # Acquire database
    db = get_db()

    curs = db.cursor()
    curs.execute(
        'SELECT p.id, username, title, imgFile, lat, lng, author_id'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE lat IS NOT NULL AND lng IS NOT NULL'
        ' ORDER BY created DESC'
    )
    posts = curs.fetchall()

    # Parse query returns
    for row in posts:
        # Assign green markers for nearby projects
        if row[0] != id:
            info = "<img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /><br /><b>"+row[2]+"(ID: "+str(row[0])+") by "+row[1]+"(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a>)</b>"
            if g.user is not None:
                if g.user[0] == row[6]:
                    info = "<img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /><br /><b>"+row[2]+"(ID: "+str(row[0])+") by "+row[1]+"(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a><a class='post-meta' href='../"+str(row[0])+"/update'>/Edit</a>)</b>"

            marker = {'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
                      'lat': row[4],
                      'lng': row[5],
                      'infobox': info}
            mapList.append(marker)
        # Assign blue marker indicating position of current project
        else:
            info = "<b>Current Project(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a>)</b>"
            if g.user is not None:
                if g.user[0] == row[6]:
                    info = "<b>Current Project(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a><a class='post-meta' href='../"+str(row[0])+"/update'>/Edit</a>)</b>"

            marker = {'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                      'lat': row[4],
                      'lng': row[5],
                      'infobox': info}
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
    curs = db.cursor()
    curs.execute(
        'SELECT p.id, title, body, created, author_id, username, imgFile, wd, ht'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id != 1'
        ' ORDER BY created DESC'
    )
    posts = curs.fetchall()

    curs.execute(
        'SELECT image, postID, width, height'
        ' FROM album'
    )
    imgs = curs.fetchall()

    return render_template('blog/index.html', posts=posts, imgs=imgs)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    db = get_db()
    curs = db.cursor()
    curs.execute(
        'SELECT image, width, height'
        ' FROM album'
        ' WHERE postID = 1'
    )
    post = curs.fetchone()

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
                curs.execute(
                    'INSERT INTO post (title, body, author_id, imgFile, wd, ht, lat, lng)'
                    ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (title, body, g.user[0], filename, request.form['width'], request.form['height'], request.form['lat'], request.form['lng'])
                    )
            else:
                curs.execute(
                    'INSERT INTO post (title, body, author_id, imgFile, wd, ht)'
                    ' VALUES (%s, %s, %s, %s, %s, %s)',
                    (title, body, g.user[0], filename, request.form['width'], request.form['height'])
                    )
            db.commit()

            #Acquire latest insert id
            curs.execute('SELECT LAST_INSERT_ID()')
            insertID = curs.fetchone()

            #Update new postID in position 0
            curs.execute(
                'UPDATE album SET postID = %s'
                ' WHERE postID = 1',
                (insertID[0],)
            )
            db.commit()

            #Create new directory for photos
            try:
                os.makedirs('flask_rephoto/flaskr/static/myImgs/'+str(insertID[0]))
            except OSError:
                pass

            shutil.move('flask_rephoto/flaskr/static/myImgs/'+filename, 'flask_rephoto/flaskr/static/myImgs/'+str(insertID[0]))

            return redirect(url_for('blog.index'))

    return render_template('blog/create.html', post=post)

def get_post(id, check_author=True):
    db = get_db()
    curs = db.cursor()
    curs.execute(
        'SELECT p.id, title, body, created, author_id, username, imgFile, wd, ht'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = %s',
        (id,)
    )
    post = curs.fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post[4] != g.user[0]:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    # Get imgs from album based on project id
    db = get_db()
    curs = db.cursor()
    curs.execute(
        'SELECT image, postID, width, height'
        ' FROM album'
        ' WHERE postID = %s',
        (id,)
    )
    imgs = curs.fetchall()

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
            # If file is real, upload and save to DB
            if changeFile:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                curs.execute(
                    'UPDATE post SET title = %s, body = %s, imgFile = %s, wd = %s, ht = %s'
                    ' WHERE id = %s',
                    (title, body, filename, request.form['width'], request.form['height'], id)
                )
            else:
                curs.execute(
                    'UPDATE post SET title = %s, body = %s'
                    ' WHERE id = %s',
                    (title, body, id)
                )

            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post, imgs=imgs)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    # Acquire database
    db = get_db()
    curs = db.cursor()
    # Delete all instances from the album
    curs.execute('DELETE FROM album WHERE postID = %s', (id,))
    db.commit()
    # Delete post itself
    curs.execute('DELETE FROM post WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/imageCapture', methods=('GET', 'POST'))
@login_required
def imageCapture(id):
    # Create New Post temp ID
    post = 1
    # If updating a post
    if id != 1:
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
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            db = get_db()
            curs = db.cursor()

            # If not new project, update existing project
            if id != 1:
                #save file
                file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/"+str(id), filename))

                #save to tables
                curs.execute(
                    'UPDATE post SET imgFile = %s, wd = %s, ht = %s'
                    ' WHERE id = %s',
                    (filename, request.form['width'], request.form['height'], id)
                )
                db.commit()

                curs.execute(
                    'INSERT INTO album (postID, image, width, height, timedate)'
                    ' VALUES (%s, %s, %s, %s, %s)',
                    (id, filename, request.form['width'], request.form['height'], datetime.now())
                )
                db.commit()
            # If new project, temporarily store picture with id 0
            else:
                #save file
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                #Clear previous just in case
                curs.execute('DELETE FROM album WHERE postID = 1')
                db.commit()
                #Temporarily store picture in album postID position 1
                curs.execute(
                    'INSERT INTO album (postID, image, width, height, timedate)'
                    ' VALUES (%s, %s, %s, %s, %s)',
                    (id, filename, request.form['width'], request.form['height'], datetime.now())
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

@bp.route('/<int:id>/detail', methods=('GET', 'POST'))
def detail(id):
    # Get post data
    post = get_post(id, False)

    # Get imgs from album based on project id
    db = get_db()
    curs = db.cursor()
    curs.execute(
        'SELECT image, postID, width, height'
        ' FROM album'
        ' WHERE postID = %s',
        (id,)
    )
    imgs = curs.fetchall()

    return render_template('blog/detail.html', post=post, imgs=imgs)

@bp.route('/<int:id>/deletePic', methods=('POST',))
@login_required
def deletePic(id):
    # Acquire database
    db = get_db()
    curs = db.cursor()

    # Delete picture from album
    curs.execute('DELETE FROM album WHERE postID = %s and image = %s', (id, request.form['picName']))
    db.commit()

    # If album is empty afterwards, delete post
    curs.execute('Select * FROM album WHERE postID = %s', (id,))
    rows = curs.fetchall()
    count = 0
    for row in rows:
        count+=1
    if count == 0:
        # Delete post itself
        curs.execute('DELETE FROM post WHERE id = %s', (id,))
        db.commit()
        return redirect(url_for('blog.index'))

    return redirect(url_for('blog.update', id=id))