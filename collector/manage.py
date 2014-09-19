# Migration manager

from flask_migrate import Migrate
from flask_migrate import MigrateCommand
from flask_script import Command
from flask_script import Manager

from collector.api import log
from collector.api.app import app
from collector.api.app import db
from collector.api.db import model


class RutTest(Command):
    """Starts test application
    """

    def run(self):
        app.config.from_object('collector.api.config.Testing')
        log.init_logger()
        app.run()


manager = Manager(app)

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command('runserver_test', RutTest())


if __name__ == '__main__':
    manager.run()
