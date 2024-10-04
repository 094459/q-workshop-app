from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:change-me@127.0.0.1/voting'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    polls = db.relationship('Poll', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.user_id)

# Poll model
class Poll(db.Model):
    __tablename__ = 'polls'
    poll_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    options = db.relationship('Option', backref='poll', cascade='all, delete-orphan', lazy='dynamic')

# Option model
class Option(db.Model):
    __tablename__ = 'poll_options'
    option_id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.poll_id'), nullable=False)
    option_text = db.Column(db.String(255), nullable=False)
    votes = db.relationship('Vote', backref='option', cascade='all, delete-orphan', lazy='dynamic')

# Vote model
class Vote(db.Model):
    __tablename__ = 'votes'
    vote_id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.poll_id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_options.option_id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    voted_at = db.Column(db.DateTime, default=db.func.current_timestamp())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    polls = Poll.query.order_by(Poll.created_at.desc()).all()
    return render_template('home.html', polls=polls)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('register'))
        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create_poll', methods=['GET', 'POST'])
@login_required
def create_poll():
    if request.method == 'POST':
        title = request.form['title']
        options = request.form.getlist('options')

        if not title.strip():
            flash('Poll title is required')
            return redirect(url_for('create_poll'))

        if len(options) < 2:
            flash('At least two options are required')
            return redirect(url_for('create_poll'))

        new_poll = Poll(title=title, user_id=current_user.user_id)

        # Add options to the poll
        for option_text in options:
            if option_text.strip() == '':
                continue  # Skip empty options
            option = Option(option_text=option_text.strip())
            new_poll.options.append(option)

        db.session.add(new_poll)
        db.session.commit()
        flash('Poll created successfully')
        return redirect(url_for('home'))
    return render_template('create_poll.html')




@app.route('/my_polls')
@login_required
def my_polls():
    user_polls = Poll.query.filter_by(user_id=current_user.user_id).order_by(Poll.created_at.desc()).all()
    return render_template('my_polls.html', polls=user_polls)

@app.route('/vote/<int:poll_id>', methods=['GET', 'POST'])
def vote(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    options = poll.options.all()
    if request.method == 'POST':
        option_id = request.form.get('option')
        if not option_id:
            flash('Please select an option to vote')
            return redirect(url_for('vote', poll_id=poll_id))

        option = Option.query.filter_by(option_id=option_id, poll_id=poll_id).first()
        if not option:
            flash('Invalid option selected')
            return redirect(url_for('vote', poll_id=poll_id))

        # Code to allow only single IPs to vote
        # ip_address = request.remote_addr
        # existing_vote = Vote.query.filter_by(poll_id=poll_id, ip_address=ip_address).first()
        # if existing_vote:
        #     flash('You have already voted in this poll')
        # else:
        #     vote = Vote(poll_id=poll_id, option_id=option_id, ip_address=ip_address)
        #     db.session.add(vote)
        #     db.session.commit()
        #     flash('Vote recorded successfully')
        ip_address = request.remote_addr
        vote = Vote(poll_id=poll_id, option_id=option_id, ip_address=ip_address)
        db.session.add(vote)
        db.session.commit()
        flash('Vote recorded successfully')
        return redirect(url_for('home'))
    return render_template('vote.html', poll=poll, options=options)

@app.route('/results/<int:poll_id>')
def results(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    # Count votes for each option
    results = db.session.query(
        Option.option_text,
        func.count(Vote.vote_id).label('vote_count')
    ).join(Vote, Vote.option_id == Option.option_id)\
     .filter(Option.poll_id == poll_id)\
     .group_by(Option.option_id, Option.option_text)\
     .all()
    
    # Calculate total votes
    total_votes = sum(result.vote_count for result in results)
    
    # Calculate percentages
    results_with_percentage = [
        {
            'option': result.option_text,
            'count': result.vote_count,
            'percentage': (result.vote_count / total_votes * 100) if total_votes > 0 else 0
        }
        for result in results
    ]
    
    return render_template('results.html', poll=poll, results=results_with_percentage, total_votes=total_votes)


if __name__ == '__main__':
    app.run(debug=True)