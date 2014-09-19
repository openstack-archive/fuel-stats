# Migration manager

from flask_migrate import Migrate
from flask_migrate import MigrateCommand
from flask_script import Manager

from collector.api import log
from collector.api.app import app
from collector.api.db.model import *


def configure_app(mode=None):
    mode_map = {
        'test': 'collector.api.config.Testing',
        'prod': 'collector.api.config.Production'
    }
    app.config.from_object(mode_map.get(mode))
    log.init_logger()
    return app


manager = Manager(configure_app)
manager.add_option('--mode', help="Acceptable modes. Default: 'test'",
                   choices=('test', 'prod'), default='test', dest='mode')

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
