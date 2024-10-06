import pytest
from app import app, db, User, Poll, PollOption, Vote

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all

def test_user_registration_success(client):
    response = client.post('/register', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'User registered successfully' in response.data
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None

def test_user_registration_duplicate_email(client):
    # Register a user
    client.post('/register', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    # Try to register with the same email
    response = client.post('/register', data={
        'email': 'test@example.com',
        'password': 'anotherpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email already registered' in response.data

def test_user_registration_missing_fields(client):
    response = client.post('/register', data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email and password are required' in response.data

def test_poll_creation_success(client):
    # Register and login a user
    client.post('/register', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })

    response = client.post('/create_poll', data={
        'title': 'Test Poll',
        'options': ['Option 1', 'Option 2', 'Option 3']
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Poll created successfully' in response.data
    poll = Poll.query.filter_by(title='Test Poll').first()
    assert poll is not None
    #assert len(poll.options) == 3
    assert poll.options.count() == 3
    

def test_poll_creation_not_logged_in(client):
    response = client.post('/create_poll', data={
        'title': 'Test Poll',
        'options': ['Option 1', 'Option 2']
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'You must be logged in to create a poll' in response.data

def test_poll_creation_missing_fields(client):
    # Register and login a user
    client.post('/register', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })

    response = client.post('/create_poll', data={
        'title': 'Test Poll',
        'options': ['Option 1']
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Title and at least two options are required' in response.data

def test_voting_success(client):
    # Register a user, create a poll, and vote
    client.post('/register', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    client.post('/create_poll', data={
        'title': 'Test Poll',
        'options': ['Option 1', 'Option 2']
    })
    poll = Poll.query.filter_by(title='Test Poll').first()
    option = poll.options[0]

    response = client.post(f'/poll/{poll.poll_id}', data={
        'option_id': option.option_id
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Vote recorded successfully' in response.data
    vote = Vote.query.filter_by(poll_id=poll.poll_id, option_id=option.option_id).first()
    assert vote is not None

def test_voting_no_option_selected(client):
    # Register a user, create a poll, and attempt to vote without selecting an option
    client.post('/register', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    client.post('/create_poll', data={
        'title': 'Test Poll',
        'options': ['Option 1', 'Option 2']
    })
    poll = Poll.query.filter_by(title='Test Poll').first()

    response = client.post(f'/poll/{poll.poll_id}', data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Please select an option' in response.data