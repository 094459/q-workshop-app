from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:change-me@127.0.0.1/voting'
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

# User registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    new_user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

# User login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.user_id
        return jsonify({'message': 'Logged in successfully'}), 200
    
    return jsonify({'message': 'Invalid email or password'}), 401

# User logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Create a new poll
@app.route('/polls', methods=['POST'])
def create_poll():
    if 'user_id' not in session:
        return jsonify({'message': 'You must be logged in to create a poll'}), 401
    
    data = request.get_json()
    title = data.get('title')
    options = data.get('options')
    
    if not title or not options or len(options) < 2:
        return jsonify({'message': 'Title and at least two options are required'}), 400
    
    new_poll = Poll(user_id=session['user_id'], title=title)
    db.session.add(new_poll)
    db.session.flush()
    
    for option_text in options:
        new_option = PollOption(poll_id=new_poll.poll_id, option_text=option_text)
        db.session.add(new_option)
    
    db.session.commit()
    
    return jsonify({'message': 'Poll created successfully', 'poll_id': new_poll.poll_id}), 201

# Vote on a poll
@app.route('/polls/<int:poll_id>/vote', methods=['POST'])
def vote_on_poll(poll_id):
    data = request.get_json()
    option_id = data.get('option_id')
    
    if not option_id:
        return jsonify({'message': 'Option ID is required'}), 400
    
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({'message': 'Poll not found'}), 404
    
    option = PollOption.query.filter_by(poll_id=poll_id, option_id=option_id).first()
    if not option:
        return jsonify({'message': 'Invalid option for this poll'}), 400
    
    ip_address = request.remote_addr
    existing_vote = Vote.query.filter_by(poll_id=poll_id, ip_address=ip_address).first()
    
    if existing_vote:
        return jsonify({'message': 'You have already voted on this poll'}), 400
    
    new_vote = Vote(poll_id=poll_id, option_id=option_id, ip_address=ip_address)
    db.session.add(new_vote)
    db.session.commit()
    
    return jsonify({'message': 'Vote recorded successfully'}), 201

# Get poll results
@app.route('/polls/<int:poll_id>/results', methods=['GET'])
def get_poll_results(poll_id):
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({'message': 'Poll not found'}), 404
    
    options = PollOption.query.filter_by(poll_id=poll_id).all()
    results = {}
    
    for option in options:
        vote_count = Vote.query.filter_by(poll_id=poll_id, option_id=option.option_id).count()
        results[option.option_text] = vote_count
    
    return jsonify({
        'poll_title': poll.title,
        'results': results
    }), 200

# List all polls
@app.route('/polls', methods=['GET'])
def list_polls():
    polls = Poll.query.all()
    poll_list = []
    
    for poll in polls:
        poll_data = {
            'poll_id': poll.poll_id,
            'title': poll.title,
            'created_at': poll.created_at.isoformat()
        }
        poll_list.append(poll_data)
    
    return jsonify({'polls': poll_list}), 200

if __name__ == '__main__':
    app.run(debug=True)