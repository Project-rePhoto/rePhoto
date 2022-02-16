import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/loginOrReg', methods=('GET', 'POST'))
def loginOrReg():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        curs = db.cursor()
        error = None

        # TODO: data sanitization (username and password)

        if request.form['bit'] == 'reg':
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            else:
                curs.execute(
                    'SELECT id FROM user WHERE username = %s', (username,)
                )
                row = curs.fetchone()
                if row is not None:
                    error = 'User {} is already registered.'.format(username)

            if error is None:
                curs.execute(
                    'INSERT INTO user (username, password) VALUES (%s, %s)',
                    (username, generate_password_hash(password))
                )
                db.commit()


                curs.execute(
                    'SELECT * FROM user WHERE username = %s', (username,)
                )
                user = curs.fetchone()
                session.clear()
                session['user_id'] = user[0]

                return redirect(url_for('blog.profile'))

            else:
                flash(error)


        elif request.form['bit'] == 'log':
            curs.execute(
                'SELECT * FROM user WHERE username = %s', (username,)
            )
            user = curs.fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif not check_password_hash(user[2], password):
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['user_id'] = user[0]
                return redirect(url_for('blog.profile'))

            flash(error)

    return render_template('auth/loginOrReg.html')

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
            return redirect(url_for('auth.loginOrReg'))

        return view(**kwargs)

    return wrapped_view