from flask_sqlalchemy import SQLAlchemy

from collector.api.app import app


db = SQLAlchemy(app)
