import os

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for
)
from flask import current_app as app

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from flaskr.auth import login_required
from flaskr.db import get_db
from flask import send_from_directory

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


bp = Blueprint('blog', __name__)

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, imgFile'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
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
                	error += 'File type is not allowed. '

        if not title:
            error += 'Title is required.'

        if error:
            flash(error)
        else:
            # save file
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id, imgFile)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], filename)
                )
            db.commit()
            return redirect(url_for('blog.index'))
		
    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, imgFile'
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
                    'UPDATE post SET title = ?, body = ?, imgFile = ?'
                    ' WHERE id = ?',
                    (title, body, filename, id)
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

@bp.route('/<int:id>/saveToAlbum', methods=('GET', 'POST'))
@login_required
def saveToAlbum(id):
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

            db.execute(
                'INSERT INTO album (userID, image)'
                ' VALUES (?, ?)',
                (id, filename)
                )
            db.commit()

            flash('Album Successfully Updated!')
        else:
            flash(error)

    return redirect(url_for('blog.update', id=id))

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))



@bp.route('/<int:id>/imageCapture', methods=('GET', 'POST'))
@login_required
def imageCapture(id):
    post = get_post(id)

    if request.method == 'POST':
        filename = ''
        error = ''

        # check if the post request has the file part
        if 'file' not in request.files:
            error += 'No file part. Chen Hao Liu'

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

            db.execute(
                'INSERT INTO album (userID, image)'
                ' VALUES (?, ?)',
                (id, filename)
                )
            db.commit()

            flash('Album Successfully Updated!')
            #return redirect(url_for('blog.index'))
        else:
            flash(error)

    return render_template('blog/imageCapture.html', post=post)