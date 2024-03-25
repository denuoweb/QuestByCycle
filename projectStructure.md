BikeHunt/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── main.py
│   │   └── profile.py
│   │
│   ├── templates/
│   │   ├── layout.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   └── submit_task.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css
│   │   ├── js/
│   │   └── img/
│   │
│   └── utils/
│       └── helpers.py
│
├── migrations/  # Generated by Flask-Migrate for database migrations
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   └── test_routes.py
│
├── .env  # Environment variables
├── config.py  # Application configuration
├── README.md
└── run.py  # Entry point to start the Flask application