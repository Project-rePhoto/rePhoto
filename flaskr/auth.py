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
        email_uid = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    # database inits
    db = get_db()
    curs = db.cursor()

    # split email and uid
    arr = email_uid.split(' ')

    # create new user
    curs.execute(
        'INSERT INTO user (username, password, email) VALUES (%s, %s, %s)',
        (arr[1], generate_password_hash(arr[2]), arr[0])
    )
    db.commit()

    # retrieve user_id and create session variable
    curs.execute(
        'SELECT * FROM user WHERE username = %s', (arr[1],)
    )
    user = curs.fetchone()
    session.clear()
    session['user_id'] = user[0]

    msg = "You have confirmed your email: %s, thanks!" % (arr[0],)
    flash(msg, 'success')
    return redirect(url_for('blog.profile'))

@bp.route('/password_reset/<token>', methods=('GET', 'POST'))
def password_reset(token):
    if request.method == 'POST':
        newpass = request.form['newPass']
        conpass = request.form['conPass']
        email_uid = request.form['email_uid']

        # authenticate token
        try:
            email_uid = confirm_token(email_uid)
        except:
            flash('The reset link is invalid or has expired.', 'danger')
            return redirect(url_for('auth.login'))

        db = get_db()
        curs = db.cursor()
        error = None

        if not newpass:
            error = 'New password is required.'
        elif not conpass:
            error = 'Please confirm new password.'
        elif newpass != conpass:
            error = 'Passwords do not match.'
        else:
            # split email and uid
            arr = email_uid.split(' ')

            curs.execute(
                'SELECT * FROM user WHERE id = %s', (int(arr[1]),)
            )
            user = curs.fetchone()

            if user is None:
                error = 'Something went wrong. This account does not exist.'
            elif check_password_hash(user[2], newpass):
                error = 'New password cannot be the same as the previous password.'
            else:
                # update password for account
                curs.execute(
                    'UPDATE user SET password = %s WHERE id = %s',
                    (generate_password_hash(newpass), user[0])
                )
                db.commit()

                # log user in
                session.clear()
                session['user_id'] = user[0]
                return redirect(url_for('blog.profile'))

        # If error, reset verification token
        email_uid = request.form['email_uid']
        flash(error)
    else:
        email_uid = token

    return render_template('auth/password_reset.html', email_uid=email_uid)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        resetEmail = request.form['resetEmail']

        db = get_db()
        curs = db.cursor()
        error = None

        # TODO: data sanitization (username and password)
        # action for registration
        if request.form['bit'] == 'reg':
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif not email:
                error = 'Email is required.'
            else:
                # check email for uniqueness
                curs.execute(
                    'SELECT id FROM user WHERE email = %s', (email,)
                )
                row = curs.fetchone()
                if row is not None:
                    error = 'Email {} is already in use.'.format(email)

                # check username for uniqueness
                curs.execute(
                    'SELECT id FROM user WHERE username = %s', (username,)
                )
                row = curs.fetchone()
                if row is not None:
                    error = 'User {} is already registered.'.format(username)

            if error is None:
                # concatenate email and user_id
                email_uid = email + " " + username + " " + password

                # send email confirmation
                token = generate_confirmation_token(email_uid)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                html = render_template('auth/activate.html', confirm_url=confirm_url)
                subject = "Please confirm your email"
                send_email(email, subject, html)

                flash('You check your email to confirm your account!', 'success')
            else:
                flash(error)

        # action for login
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

        # action for password reset
        elif request.form['bit'] == 'res':
            # check email for uniqueness
            curs.execute(
                'SELECT id FROM user WHERE email = %s', (resetEmail,)
            )
            row = curs.fetchone()

            if row is None:
                error = 'Email {} is not recognized.'.format(resetEmail)
                flash(error)
            else:
                # concatenate email and user_id
                email_uid = resetEmail + " " + str(row[0])

                # send email confirmation
                token = generate_confirmation_token(email_uid)
                confirm_url = url_for('auth.password_reset', token=token, _external=True)
                html = render_template('auth/reset.html', confirm_url=confirm_url)
                subject = "Password Reset"
                send_email(resetEmail, subject, html)

                flash('Please check your email to reset your password!', 'success')

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