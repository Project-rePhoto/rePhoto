import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from flask import send_file
from flask import current_app as app
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flaskr.auth import login_required
from flaskr.db import get_db
#Google Maps API
from flask_googlemaps import Map
#import Geocoder
#from flaskr import simple_geoip
from datetime import datetime
#import Cloud Vision API
from google.cloud import vision

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

bp = Blueprint('blog', __name__)

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#def getGeoIP():
    #retrieve geoip data for the given requester
#    geoip_data = simple_geoip.get_geoip_data()
#    return geoip_data

def retrieveCVResults(type, image_uri):
    #retrieve Cloud Vision results for image
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = image_uri

    if type == 0: # basic label detection
        return client.label_detection(image=image)
    elif type == 1: # text detection
        return client.text_detection(image=image)
    else: # landmark_detection
        return client.landmark_detection(image=image)

@bp.route('/<int:id>/setMap', methods=('GET', 'POST'))
def setMap(id):
    mapList = []
    latitude = 0
    longitude = 0

    # Acquire database
    db = get_db()

    curs = db.cursor()
    curs.execute(
        'SELECT p.id, username, title, imgFile, lat, lng, author_id, archive'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE lat IS NOT NULL AND lng IS NOT NULL'
        ' ORDER BY created DESC'
    )
    posts = curs.fetchall()
    posts = list(map(list, posts))

    # convert from archive url to folder location
    for row in posts:
        # check that image is part of archives
        if row[7] == 1:
            if row[3] is not None:
                if len(row[3]) > 10:
                    if row[3][0:10] == "/baseImage":
                        num = 0
                        pic = ""
                        for i in row[3]:
                            if num == 3:
                                pic = pic + i
                            if i == '/':
                                num+=1
                        row[3] = pic
                    elif row[3][0:4] == "http":
                        num = 0
                        pic = ""
                        for i in row[3]:
                            if num == 5:
                                pic = pic + i
                            if i == '/':
                                num+=1
                        row[3] = pic

    # Parse query returns
    for row in posts:
        # Assign green markers for nearby projects
        if row[0] != id:
            info = "<img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /><br /><b>"+row[2]+"(ID: "+str(row[0])+") by "+row[1]+"(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a>)</b>"
            if g.user is not None:
                if g.user[0] == row[6]:
                    info = "<img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /><br /><b>"+row[2]+"(ID: "+str(row[0])+") by "+row[1]+"(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a><a class='post-meta' href='../"+str(row[0])+"/update'>/Edit</a>)</b>"
            if row[7] == 1:
                info = "<img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /><br /><b>"+row[2]+"(ID: "+str(row[0])+") by "+row[1]+"(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a>)</b>"
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
            if row[7] == 1:
                info = "<img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /><br /><b>"+row[2]+"(ID: "+str(row[0])+") by "+row[1]+"(<a class='post-meta' href='../"+str(row[0])+"/detail'>View</a>)</b>"
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

@bp.route('/projmap', methods=('GET', 'POST'))
def projmap():
    # Acquire database
    db = get_db()

    curs = db.cursor()
    curs.execute(
        'SELECT p.id, username, title, imgFile, lat, lng, author_id, archive'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE lat IS NOT NULL AND lng IS NOT NULL'
        ' ORDER BY created DESC'
    )
    posts = curs.fetchall()
    posts = list(map(list, posts))

    # convert from archive url to folder location
    for row in posts:
        # check that image is part of archives
        if row[7] == 1:
            if row[3] is not None:
                if len(row[3]) > 10:
                    if row[3][0:10] == "/baseImage":
                        num = 0
                        pic = ""
                        for i in row[3]:
                            if num == 3:
                                pic = pic + i
                            if i == '/':
                                num+=1
                        row[3] = pic
                    elif row[3][0:4] == "http":
                        num = 0
                        pic = ""
                        for i in row[3]:
                            if num == 5:
                                pic = pic + i
                            if i == '/':
                                num+=1
                        row[3] = pic

        if g.user is not None:
            if g.user[0] == row[6]:
                row[3] = "<h4>Click To Contribute Image to Project</h4><br/><a href='../"+str(row[0])+"/imageCapture'><img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /></a><br /><b>"+row[2]+" (ID: "+str(row[0])+") by "+row[1]+"</b><br/><h4>(<a class='post-meta' href='../"+str(row[0])+"/update'>Click to Edit Project</a>)</h4>"
            else:
                # include html script for displaying image
                row[3] = "<h4>Click To Contribute Image to Project</h4><br/><a href='../"+str(row[0])+"/imageCapture'><img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /></a><br /><b>"+row[2]+" (ID: "+str(row[0])+") by "+row[1]+"</b><br/><h4>(<a class='post-meta' href='../"+str(row[0])+"/detail'>Click to View Project</a>)</h4>"
        else:
            # include html script for displaying image
            row[3] = "<h4>Click To Contribute Image to Project</h4><br/><a href='../"+str(row[0])+"/imageCapture'><img src='/static/myImgs/"+str(row[0])+"/"+row[3]+"' /></a><br /><b>"+row[2]+" (ID: "+str(row[0])+") by "+row[1]+"</b><br/><h4>(<a class='post-meta' href='../"+str(row[0])+"/detail'>Click to View Project</a>)</h4>"
    return render_template('blog/projmap.html', posts=posts)

@bp.route('/')
def redirectIndex():
    return redirect(url_for('blog.projmap'))

@bp.route('/<int:count>/<string:searchTerm>/index', methods=('GET','POST'))
def index(count, searchTerm):
    db = get_db()
    curs = db.cursor()

    if searchTerm == "general":
        curs.execute(
            'SELECT p.id, title, body, created, author_id, username, imgFile, wd, ht, archive'
            ' FROM post p JOIN user u ON p.author_id = u.id'
            ' WHERE p.id != 1'
            ' ORDER BY created DESC'
            ' LIMIT 5 OFFSET %s',
            (count)
        )
    else:
        newTerm = '%%' + searchTerm + '%%'
        curs.execute(
            'SELECT p.id, title, body, created, author_id, username, imgFile, wd, ht, archive'
            ' FROM post p JOIN user u ON p.author_id = u.id'
            ' WHERE p.id != 1 AND (title LIKE %s OR body LIKE %s OR tag LIKE %s)'
            ' ORDER BY created DESC'
            ' LIMIT 5 OFFSET %s',
            (newTerm, newTerm, newTerm, count)
        )
    posts = curs.fetchall()
    posts = list(map(list, posts))

    # convert from archive url to folder location
    for row in posts:
        # check that image is part of archives
        if row[9] == 1:
            if row[6] is not None:
                if len(row[6]) > 10:
                    if row[6][0:10] == "/baseImage":
                        num = 0
                        pic = ""
                        for i in row[6]:
                            if num == 3:
                                pic = pic + i
                            if i == '/':
                                num+=1
                        row[6] = pic
                    elif row[6][0:4] == "http":
                        num = 0
                        pic = ""
                        for i in row[6]:
                            if num == 5:
                                pic = pic + i
                            if i == '/':
                                num+=1
                        row[6] = pic

    curs.execute(
        'SELECT image, postID, width, height'
        ' FROM album'
    )
    imgs = curs.fetchall()
    imgs = list(map(list, imgs))

    # similarly, do so for album
    for row in imgs:
        if row[0] is not None:
            if len(row[0]) > 10:
                if row[0][0:4] == "http":
                    num = 0
                    pic = ""
                    for i in row[0]:
                        if num == 6:
                            pic = pic + i
                        if i == '/':
                            num+=1
                    row[0] = pic

    # Track contributions
    beg=mid=adv=0
    if g.user is not None:
        curs.execute(
            'SELECT contributions'
            ' FROM user u'
            ' WHERE u.id = %s',
            (g.user[0],)
        )
        conts = curs.fetchone()

        if conts[0] <= 10:
            beg = conts[0]
        elif conts[0] <= 40:
            beg = 10
            mid = conts[0]-10
        else:
            beg = 10
            mid = 30
            adv = conts[0]-40

    return render_template('blog/index.html', posts=posts, imgs=imgs, count=count, searchTerm=searchTerm, beg=beg, mid=mid, adv=adv)

@bp.route('/<int:id>/create', methods=('GET', 'POST'))
@login_required
def create(id):
    db = get_db()
    curs = db.cursor()
    curs.execute(
        'SELECT image, width, height, postID'
        ' FROM album'
        ' WHERE postID = %s',
        (id,)
    )
    post = curs.fetchone()

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = ''

        #Start here
        if not title:
            error += 'Title is required.'

        if error:
            flash(error)
        else:
            # Update title, body, etc.
            db = get_db()
            curs.execute(
                'UPDATE post SET title = %s, body = %s, author_id = %s, lat = %s, lng = %s'
                ' WHERE id = %s',
                (title, body, g.user[0], request.form['lat'], request.form['lng'], id)
                )
            db.commit()

            return redirect(url_for('blog.index', count=0, searchTerm='general'))

    return render_template('blog/create.html', post=post)

def get_post(id, check_author=True):
    db = get_db()
    curs = db.cursor()
    curs.execute(
        'SELECT p.id, title, body, created, author_id, username, imgFile, wd, ht, archive, tag'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = %s',
        (id,)
    )
    post = curs.fetchone()
    post = list(post)

    # reformat archive img url
    if post[6] is not None:
        if len(post[6]) > 10:
            if post[6][0:10] == "/baseImage":
                num = 0
                pic = ""
                for i in post[6]:
                    if num == 3:
                        pic = pic + i
                    if i == '/':
                        num+=1
                post[6] = pic
            elif post[6][0:4] == "http":
                num = 0
                pic = ""
                for i in post[6]:
                    if num == 5:
                        pic = pic + i
                    if i == '/':
                        num+=1
                post[6] = pic

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
    imgs = list(map(list, imgs))

    # reformat archive img url
    for row in imgs:
        if row[0] is not None:
            if len(row[0]) > 10:
                if row[0][0:4] == "http":
                    num = 0
                    pic = ""
                    for i in row[0]:
                        if num == 6:
                            pic = pic + i
                        if i == '/':
                            num+=1
                    row[0] = pic

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
                file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/"+str(id), filename))

                # ------- Retrieve Vision API result -------
                image_uri = 'https://liuchao.pythonanywhere.com/static/myImgs/'+str(id)+'/'+filename
                response = retrieveCVResults(0, image_uri)

                # Retrieve current post tags
                curs.execute(
                    'SELECT tag'
                    ' FROM post'
                    ' WHERE id = %s',
                    (id,)
                )
                tagPost = curs.fetchone()
                tags = tagPost[0]
                albumTag = ["General"]

                #Split string and add elements to set
                tagArr = tags.split('|')
                tagSet = set()
                for i in tagArr:
                    tagSet.add(i)

                # Append new tags
                labelList = [tags]
                for label in response.label_annotations:
                    if label.score > 0.7:
                        albumTag.append(label.description)
                        if label.description not in tagSet:
                            labelList.append(label.description)

                # Retrieve text detection
                textResponse = retrieveCVResults(1, image_uri)

                # Append new tags for text
                for text in textResponse.text_annotations:
                    albumTag.append(text.description)
                    if text.description not in tagSet:
                        labelList.append(text.description)

                tagList = "|".join(labelList)
                albumList = "|".join(albumTag)
                # ----------------------------------------

                curs.execute(
                    'UPDATE post SET title = %s, body = %s, imgFile = %s, wd = %s, ht = %s, tag = %s'
                    ' WHERE id = %s',
                    (title, body, filename, request.form['width'], request.form['height'], tagList, id)
                )
                db.commit()
                # Save for album
                curs.execute(
                    'INSERT INTO album (postID, image, width, height, timedate, tag, name)'
                    ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (id, filename, request.form['width'], request.form['height'], datetime.now(), albumList, request.form['name'])
                )
                db.commit()
            else:
                curs.execute(
                    'UPDATE post SET title = %s, body = %s'
                    ' WHERE id = %s',
                    (title, body, id)
                )
                db.commit()
            return redirect(url_for('blog.index', count=0, searchTerm='general'))

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
    return redirect(url_for('blog.index', count=0, searchTerm='general'))

@bp.route('/<int:id>/imageCapture', methods=('GET', 'POST'))
def imageCapture(id):
    # If updating a post
    if id != 1:
        post = get_post(id, False)
    else:
        post = id

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
            db = get_db()
            curs = db.cursor()

            # If not new project, update existing project
            if id != 1:
                #save file
                file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/"+str(id), filename))

                # ------- Retrieve Vision API result -------
                image_uri = 'https://liuchao.pythonanywhere.com/static/myImgs/'+str(id)+'/'+filename
                response = retrieveCVResults(0, image_uri)

                # Retrieve current post tags
                curs.execute(
                    'SELECT tag'
                    ' FROM post'
                    ' WHERE id = %s',
                    (id,)
                )
                tagPost = curs.fetchone()
                tags = tagPost[0]
                albumTag = ["General"]

                #Split string and add elements to set
                tagArr = tags.split('|')
                tagSet = set()
                for i in tagArr:
                    tagSet.add(i)

                # Append new tags
                labelList = [tags]
                for label in response.label_annotations:
                    if label.score > 0.7:
                        albumTag.append(label.description)
                        if label.description not in tagSet:
                            labelList.append(label.description)

                # Retrieve text detection
                textResponse = retrieveCVResults(1, image_uri)

                # Append new tags for text
                for text in textResponse.text_annotations:
                    albumTag.append(text.description)
                    if text.description not in tagSet:
                        labelList.append(text.description)

                tagList = "|".join(labelList)
                albumList = "|".join(albumTag)
                # ----------------------------------------

                #save to tables
                curs.execute(
                    'UPDATE post SET imgFile = %s, wd = %s, ht = %s, tag = %s'
                    ' WHERE id = %s',
                    (filename, request.form['width'], request.form['height'], tagList, id)
                )
                db.commit()

                if g.user is not None:
                    #update contributions
                    curs.execute(
                        'SELECT contributions'
                        ' FROM user u'
                        ' WHERE u.id = %s',
                        (g.user[0],)
                    )
                    conts = curs.fetchone()

                    curs.execute(
                        'UPDATE user SET contributions = %s'
                        ' WHERE id = %s',
                        (conts[0]+1, g.user[0])
                    )
                    db.commit()

                    # Save for album
                    curs.execute(
                        'INSERT INTO album (postID, image, width, height, takerID, timedate, tag, name)'
                        ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (id, filename, request.form['width'], request.form['height'], g.user[0], datetime.now(), albumList, request.form['name'])
                    )
                else:
                    # Save for album
                    curs.execute(
                        'INSERT INTO album (postID, image, width, height, timedate, tag, name)'
                        ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (id, filename, request.form['width'], request.form['height'], datetime.now(), albumList, request.form['name'])
                    )
                db.commit()

                flash('Album Successfully Updated!')
                return jsonify(id)

            # If new project, temporarily store picture with id 0
            else:
                # Time of creation
                currTime = datetime.now()

                # Save to post
                curs.execute(
                    'INSERT INTO post (created, imgFile, wd, ht, archive)'
                    ' VALUES (%s, %s, %s, %s, %s)',
                    (currTime, filename, request.form['width'], request.form['height'], 2)
                )
                db.commit()

                #Acquire latest insert id
                curs.execute('SELECT LAST_INSERT_ID()')
                insertID = curs.fetchone()

                #Create new directory for photos
                try:
                    os.makedirs('rePhoto/flaskr/static/myImgs/'+str(insertID[0]))
                except OSError:
                    pass

                #save file
                file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/"+str(insertID[0]), filename))

                #------ Retrieve Vision API result and update tags -------
                image_uri = 'https://liuchao.pythonanywhere.com/static/myImgs/'+str(insertID[0])+'/'+filename

                # Retrieve labels
                response = retrieveCVResults(0, image_uri)
                tagList = ["General"]

                # Append new tags for labels
                for label in response.label_annotations:
                    # if the match percentage is above 70%
                    if label.score > 0.7:
                        tagList.append(label.description)

                # Retrieve text detection
                textResponse = retrieveCVResults(1, image_uri)

                # Append new tags for text
                for text in textResponse.text_annotations:
                    tagList.append(text.description)

                tags = "|".join(tagList)

                #update post
                curs.execute(
                    'UPDATE post SET tag = %s'
                    ' WHERE id = %s',
                    (tags, insertID[0])
                )
                db.commit()
                #---------------------------------------------------------
                # Save for album
                curs.execute(
                    'INSERT INTO album (postID, image, width, height, takerID, timedate, tag, name)'
                    ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (insertID[0], filename, request.form['width'], request.form['height'], g.user[0], currTime, tags, request.form['name'])
                )
                db.commit()

                flash('Album Successfully Updated!')
                return jsonify(insertID[0])
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

    #Split string and add elements to set
    tagArr = post[10].split('|')

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
    imgs = list(map(list, imgs))

    # reformat archive img url
    for row in imgs:
        if row[0] is not None:
            if len(row[0]) > 10:
                if row[0][0:4] == "http":
                    num = 0
                    pic = ""
                    for i in row[0]:
                        if num == 6:
                            pic = pic + i
                        if i == '/':
                            num+=1
                    row[0] = pic

    return render_template('blog/detail.html', post=post, imgs=imgs, tagArr = tagArr)

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
        return redirect(url_for('blog.index', count=0, searchTerm='general'))

    return redirect(url_for('blog.update', id=id))

@bp.route('/createFile', methods=('GET', 'POST'))
@login_required
def createFile():
    path = "static/myImgs/photolinks.txt"
    homepath = "/home/liuchao/rePhoto/flaskr/static/myImgs/photolinks.txt"

    if os.path.isfile(homepath):
        return send_file(path, as_attachment=True)

    db = get_db()
    curs = db.cursor()

    curs.execute(
        'SELECT id, imgFile'
        ' FROM post'
        ' WHERE author_id = 1'
    )
    posts = curs.fetchall()

    for row in posts:
        rowID = row[0]
        img = row[1]
        with open("rePhoto/flaskr/static/myImgs/photolinks.txt", "a") as fo:
            fo.write(str(rowID) + "\n")
            if img is not None:
                if img[0:10] == "/baseImage":
                    fo.write("http://projectrephoto.com" + img + "\n")
                else:
                    fo.write(img + "\n")
        curs.execute(
            'SELECT image'
            ' FROM album'
            ' WHERE postID = %s',
            (rowID,)
        )
        albums = curs.fetchall()
        for pic in albums:
            with open("rePhoto/flaskr/static/myImgs/photolinks.txt", "a") as pc:
                if pic[0][0:10] == "/baseImage":
                    pc.write("http://projectrephoto.com" + pic[0] + "\n")
                else:
                    pc.write(pic[0] + "\n")

    return send_file(path, as_attachment=True)

