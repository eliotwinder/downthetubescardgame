from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, socketio
from forms import LoginForm
from models import Player, Game
from flask.ext.socketio import SocketIO, emit, send, join_room, leave_room, close_room, disconnect

players = Player.query.all()
logged_in_players = 0
namespace = '/test'

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', players=players)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Player.query.filter(Player.name == form.name.data).first()
        login_user(user, remember=True)
        flash('Logged in!')
        Game.increment_counter()
        return redirect(url_for('index'))
    else:
        flash('not logged in')
    return render_template('login.html',
                           title="sign in",
                           form=form,
                           players=players)

@app.route('/logout')
def logout():
    Game.decrement_counter()
    logout_user()
    return redirect(url_for('index'))

@lm.user_loader
def load_user(id):
    return Player.query.get(int(id))

@socketio.on('user_connected', namespace=namespace)
def test_broadcast_message(message):
    emit('my response',
         {'data': message['data']},
         broadcast=True)

@socketio.on('send_chat', namespace=namespace)
def test_broadcast_message(message):
    emit('my response',
         {'data': message['data']},
         broadcast=True)