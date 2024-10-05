from flask import Flask, make_response, request, jsonify, session, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import csv
from io import StringIO
from flask import send_file

app = Flask(__name__)


# Construct the database URI using environment variables
db_user = os.environ.get('DB_USER', 'postgres')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST', '127.0.0.1')
db_name = os.environ.get('DB_NAME', 'voting')

if not db_password:
    raise ValueError("Database password not set in environment variables")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)

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
    created_at = db.Column(db.DateTime, server_default=db.func.now())

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
    voted_at = db.Column(db.DateTime, server_default=db.func.now())

# Yoda Wisdom - create a function that will return a single, random quote of wisdom from Master Yoda

def get_yoda_wisdom():
    import random
    yoda_wisdom = [
        "The greatest teacher, failure is.",
        "Fear is the path to the dark side. Fear leads to anger. Anger leads to hate. Hate leads to suffering.",
        "In a dark place we find ourselves, and a little more knowledge lights our way.",
        "Always pass on what you have learned.",
        "Truly wonderful, the mind of a child is.",
        "No. Try not. Do. Or do not. There is no try.",
        "Size matters not. Look at me. Judge me by my size, do you?",
        "Do or do not. There is no try.",
        "You must unlearn what you have learned.",
        "The ability to speak does not make you intelligent.",
        "The greatest teacher failure is.",
        "You must unlearn what you have learned.",
        "In a dark place we find ourselves, and a little more knowledge lights our way.",
        "Always pass on what you have learned.",
        "Truly wonderful, the mind of a child is.",
        "No. Try not. Do. Or do not. There is no try.",
        "Size matters not. Look at me. Judge me by my size, do you?"]
    return random.choice(yoda_wisdom)


# Routes
@app.route('/')
def index():
    polls = Poll.query.all()
    return render_template('index.html', polls=polls)


# Add a route for /about that will display a new html page called about.html that includes a quote from the get_yoda_wisdom function
@app.route('/about')
def about():
    wisdom = get_yoda_wisdom()
    return render_template('about.html', wisdom=wisdom)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        new_user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        
        flash('User registered successfully', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/create_poll', methods=['GET', 'POST'])
def create_poll():
    if 'user_id' not in session:
        flash('You must be logged in to create a poll', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        options = request.form.getlist('options')
        
        if not title or not options or len(options) < 2:
            flash('Title and at least two options are required', 'error')
            return redirect(url_for('create_poll'))
        
        new_poll = Poll(user_id=session['user_id'], title=title)
        db.session.add(new_poll)
        db.session.flush()
        
        for option_text in options:
            if option_text.strip():
                new_option = PollOption(poll_id=new_poll.poll_id, option_text=option_text)
                db.session.add(new_option)
        
        db.session.commit()
        
        flash('Poll created successfully', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_poll.html')

@app.route('/poll/<int:poll_id>', methods=['GET', 'POST'])
def view_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    options = PollOption.query.filter_by(poll_id=poll_id).all()
    
    if request.method == 'POST':
        option_id = request.form.get('option_id')
        
        if not option_id:
            flash('Please select an option', 'error')
            return redirect(url_for('view_poll', poll_id=poll_id))
        
        ip_address = request.remote_addr
        existing_vote = Vote.query.filter_by(poll_id=poll_id, ip_address=ip_address).first()
        
        # if existing_vote:
        #     flash('You have already voted on this poll', 'error')
        #     return redirect(url_for('view_poll', poll_id=poll_id))
        
        new_vote = Vote(poll_id=poll_id, option_id=option_id, ip_address=ip_address)
        db.session.add(new_vote)
        db.session.commit()
        
        flash('Vote recorded successfully', 'success')
        return redirect(url_for('view_results', poll_id=poll_id))
    return render_template('view_poll.html', poll=poll, options=options)

@app.route('/poll/<int:poll_id>/results')
def view_results(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    options = PollOption.query.filter_by(poll_id=poll_id).all()
    results = {}
    
    for option in options:
        vote_count = Vote.query.filter_by(poll_id=poll_id, option_id=option.option_id).count()
        results[option.option_text] = vote_count

    return render_template('view_results.html', poll=poll, results=results)


@app.route('/poll/<int:poll_id>/export')
def export_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    options = PollOption.query.filter_by(poll_id=poll_id).all()
    votes = Vote.query.filter_by(poll_id=poll_id).all()

    # Create a StringIO object to write CSV data
    si = StringIO()
    cw = csv.writer(si)

    # Write header
    cw.writerow(['Poll Title', poll.title])


    # Write data
    for option in options:
        vote_count = sum(1 for vote in votes if vote.option_id == option.option_id)
        cw.writerow([option.option_text, vote_count])

    # Create response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=poll_{poll_id}_results.csv"
    output.headers["Content-type"] = "text/csv"

    return output


if __name__ == '__main__':
    app.run(debug=True)
