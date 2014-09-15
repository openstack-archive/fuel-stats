from collector.app import app


@app.route('/ping')
def ping():
    return 'ok'
