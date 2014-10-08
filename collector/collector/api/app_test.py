from collector.api.app import app
from collector.api import log


app.config.from_object('collector.api.config.Testing')
log.init_logger()
