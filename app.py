from flask import Flask, flash, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:change-me@127.0.0.1/voting'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Models
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Poll(db.Model):
    __tablename__ = 'polls'
    poll_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    options = db.relationship('PollOption', backref='poll', lazy='dynamic')

class PollOption(db.Model):
    __tablename__ = 'poll_options'
    option_id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.poll_id'))
    option_text = db.Column(db.String(255), nullable=False)


class Vote(db.Model):
    __tablename__ = 'votes'
    vote_id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.poll_id'))
    option_id = db.Column(db.Integer, db.ForeignKey('poll_options.option_id'))
    ip_address = db.Column(db.String(45), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def home():
    polls = Poll.query.all()
    return render_template('home.html', polls=polls)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route('/create_poll', methods=['GET', 'POST'])
def create_poll():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        options = request.form.getlist('options')
        
        # Validate number of options
        if len(options) < 2 or len(options) > 5:
            return "A poll must have between 2 and 5 options", 400

        try:
            # Start a transaction
            db.session.begin_nested()

            # Create the poll
            poll = Poll(user_id=session['user_id'], title=title)
            logger.debug(f"Creating poll with title: {title} and options: {options}")
            db.session.add(poll)
            db.session.flush()  # This assigns an ID to the poll

            # Create the options
            for option_text in options:
                poll_option = PollOption(poll_id=poll.poll_id, option_text=option_text)
                db.session.add(poll_option)
                logger.debug(f"Created option: {option_text} for poll ID: {poll.poll_id}")

            # Commit the transaction
            db.session.commit()
            logger.debug(f"Created poll with ID: {poll.poll_id}")
            return redirect(url_for('view_poll', poll_id=poll.poll_id))

        except IntegrityError as e:
            db.session.rollback()
            print(f"Error creating poll: {str(e)}")
            return "Error creating poll. Please try again.", 500
    
    return render_template('create_poll.html')


@app.route('/poll/<int:poll_id>')
def view_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    options = PollOption.query.filter_by(poll_id=poll_id).all()
    return render_template('view_poll.html', poll=poll, options=options)

@app.route('/vote/<int:poll_id>', methods=['POST'])
def vote(poll_id):
    option_id = request.form.get('option')
    ip_address = request.remote_addr

    # Validate that an option was selected
    if not option_id:
        flash('No option selected.', 'error')
        return redirect(url_for('view_poll', poll_id=poll_id))

    # Validate that the option exists for this poll
    option = PollOption.query.filter_by(option_id=option_id, poll_id=poll_id).first()
    if not option:
        flash('Invalid option selected.', 'error')
        return redirect(url_for('view_poll', poll_id=poll_id))

    # Check if the user has already voted from this IP address
    # existing_vote = Vote.query.filter_by(poll_id=poll_id, ip_address=ip_address).first()
    # if existing_vote:
    #     flash('You have already voted on this poll.', 'error')
    #     return redirect(url_for('results', poll_id=poll_id))

    # Create a new vote
    new_vote = Vote(poll_id=poll_id, option_id=option_id, ip_address=ip_address)
    db.session.add(new_vote)

    try:
        db.session.commit()
        flash('Your vote has been recorded!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('There was an error recording your vote. Please try again.', 'error')
        return redirect(url_for('view_poll', poll_id=poll_id))

    return redirect(url_for('results', poll_id=poll_id))



@app.route('/results/<int:poll_id>')
def results(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    options = PollOption.query.filter_by(poll_id=poll_id).all()
    results = {}
    total_votes = 0
    for option in options:
        count = Vote.query.filter_by(poll_id=poll_id, option_id=option.option_id).count()
        results[option.option_text] = count
        total_votes += count
    
    # Calculate percentages
    for option in results:
        if total_votes > 0:
            results[option] = {
                'count': results[option],
                'percentage': (results[option] / total_votes) * 100
            }
        else:
            results[option] = {'count': 0, 'percentage': 0}
    
    return render_template('results.html', poll=poll, results=results, total_votes=total_votes)



if __name__ == '__main__':
    app.run(debug=True)
