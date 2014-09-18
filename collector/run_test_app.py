#!/usr/bin/env python

from collector.api.app import app
from collector.api.log import init_logger

app.config.from_object('collector.api.config.Testing')
init_logger()
app.run()
