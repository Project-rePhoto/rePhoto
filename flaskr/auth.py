import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from .config import pass_salt, secret_key, org_email
from flask import current_app as app

bp = Blueprint('auth', __name__, url_prefix='/auth')

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt=pass_salt)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        # attempt to retrieve email/check expiration
        email = serializer.loads(
            token,
            salt=pass_salt,
            max_age=expiration
        )
    except:
        return False
    return email

def send_email(to, subject, template):
    mail = Mail(app)

    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=org_email
    )
    mail.send(msg)

@bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return render_template('auth/login.html')

    # database inits
    db = get_db()
    curs = db.cursor()
    user_id = session.get('user_id')

    # Update email in user account
    curs.execute(
        'UPDATE user SET email = %s'
        ' WHERE id = %s',
        (email, user_id)
    )
    db.commit()

    flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('blog.profile'))

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        db = get_db()
        curs = db.cursor()
        error = None

        # TODO: data sanitization (username and password)
        if request.form['bit'] == 'reg':
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif not email:
                error = 'Email is required.'
            else:
                curs.execute(
                    'SELECT id FROM user WHERE username = %s', (username,)
                )
                row = curs.fetchone()
                if row is not None:
                    error = 'User {} is already registered.'.format(username)

            if error is None:
                # create new user
                curs.execute(
                    'INSERT INTO user (username, password) VALUES (%s, %s)',
                    (username, generate_password_hash(password))
                )
                db.commit()

                # retrieve user_id and create session variable
                curs.execute(
                    'SELECT * FROM user WHERE username = %s', (username,)
                )
                user = curs.fetchone()
                session.clear()
                session['user_id'] = user[0]

                # send email confirmation
                token = generate_confirmation_token(email)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                html = render_template('auth/activate.html', confirm_url=confirm_url)
                subject = "Please confirm your email"
                send_email(email, subject, html)
            else:
                flash(error)


        elif request.form['bit'] == 'log':
            curs.execute(
                'SELECT * FROM user WHERE username = %s', (username,)
            )
            user = curs.fetchone()

            if user is None:
                error = 'Incorrect username or password.'
            elif not check_password_hash(user[2], password):
                error = 'Incorrect username or password.'

            if error is None:
                session.clear()
                session['user_id'] = user[0]
                return redirect(url_for('blog.profile'))

            flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        curs = get_db().cursor()
        curs.execute('SELECT * FROM user WHERE id = %s', (user_id,))
        g.user = curs.fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view