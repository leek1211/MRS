from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for
from werkzeug import check_password_hash, generate_password_hash

from app import db
from app.forms.user import RegisterForm, LoginForm
from app.models import User
from app.decorators.user import requires_login

mod = Blueprint('user', __name__)

@mod.before_request
def before_request():
  """
  pull user's profile from the database before every request are treated
  """
  g.user = None
  if 'user_id' in session:
    g.user = User.query.get(session['user_id'])

@mod.route('/login/', methods=['GET', 'POST'])
def login():
  """
  Login form
  """
  if 'user_id' in session:
      return redirect(url_for('home'))

  form = LoginForm(request.form)
  # make sure data are valid, but doesn't validate password is right
  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data).first()
    # we use werzeug to validate user's password
    if user and check_password_hash(user.password, form.password.data):
      # the session can't be modified as it's signed, 
      # it's a safe place to store the user id
      session['user_id'] = user.id
      flash('Welcome %s' % user.name)
      return redirect(url_for('home'))
    flash('Wrong email or password', 'error-message')
  return render_template("user/login.html", form=form)

@mod.route('/register/', methods=['GET', 'POST'])
def register():
  """
  Registration Form
  """
  form = RegisterForm(request.form)
  if form.validate_on_submit():
    # create an user instance not yet stored in the database
    user = User(name=form.name.data, email=form.email.data, \
      password=generate_password_hash(form.password.data))
    # Insert the record in our database and commit it
    db.session.add(user)
    db.session.commit()

    # Log the user in, as he now has an id
    session['user_id'] = user.id

    # flash will display a message to the user
    flash('Thanks for registering')
    # redirect user to the 'home' method of the user module.
    return redirect(url_for('user.login'))
  return render_template("user/register.html", form=form)

@mod.route('/logout/', methods=['POST'])
@requires_login
def logout():
    session.pop('user_id', None)
    flash('You were logged out')
    return redirect(url_for('home'))

@mod.route('/profile/<userid>')
@requires_login
def user_profile(userid):
    user = User.query.filter_by(id=userid).first_or_404() 
    reviewed_movies = map(lambda x: x.get_movie().info(), user.reviews)
    for (m,r) in zip(reviewed_movies, user.reviews) :
        m['rating'] = r.rating


    return render_template('user/profile.html', user=user, movies = reviewed_movies)

