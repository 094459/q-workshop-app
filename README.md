# Yoda Polls

Yoda Polls is a web application that allows users to create and participate in polls, with a touch of Yoda's wisdom.

## Features

- User registration and login
- Create polls with multiple options
- Vote on polls
- View poll results
- Get random Yoda wisdom quotes

## Requirements

- Python 3.7+
- PostgreSQL database

## How to Run

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up the PostgreSQL database:
   - Install PostgreSQL if not already installed
   - Create a new database for the project
   - Set the following environment variables:
     ```
     export DB_USER=your_db_user
     export DB_PASSWORD=your_db_password
     export DB_HOST=your_db_host
     export DB_NAME=your_db_name
     ```
4. Initialize the database:
   - Connect to your PostgreSQL server and create a new database:
     ```
     createdb yoda_polls
     ```
   - Use the provided SQL script to create the necessary tables:
     ```
     psql -d yoda_polls -f data/voting-app.sql
     ```
5. Run the application:
   ```
   flask run
   ```
6. Open a web browser and navigate to `http://localhost:5000`

## How to Use

1. Register for an account or log in if you already have one
2. Create a new poll by clicking on the "Create Poll" button
3. Vote on existing polls
4. View poll results
5. Visit the About page to get some Yoda wisdom

## Technologies Used

- Flask
- SQLAlchemy
- Werkzeug

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
