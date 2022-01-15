import os
import webbrowser
from threading import Thread
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, render_template, url_for

load_dotenv()


class PyPew:
    def __init__(self):
        self.app: Optional[Flask] = None
        self.thread: Optional[Thread] = None


def create_app(pypew: Optional[PyPew] = None) -> Flask:
    app = Flask(__name__)

    app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    @app.route('/')
    def index_view():
        return render_template('index.html')

    if pypew is not None:
        pypew.app = app

    return app


def main(debug=False):
    pypew = PyPew()
    app = create_app(pypew)

    if debug:
        app.run(load_dotenv=True)

    else:
        pypew.thread = Thread(
            target=lambda: app.run(debug=False, load_dotenv=True)
        )
        pypew.thread.start()
        with app.app_context():
            webbrowser.open(url_for('index_view'))
        pypew.thread.join()


if __name__ == '__main__':
    main()
