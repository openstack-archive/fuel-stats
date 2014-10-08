from collector.api import log
from collector.api.app import app


app.config.from_object('collector.api.config.Testing')
log.init_logger()
