import os
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()


class PyPew:
    def __init__(self):
        self.app: Optional[Flask] = None


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


def main():
    pypew = PyPew()
    app = create_app(pypew)
    app.run(load_dotenv=True)


if __name__ == '__main__':
    main()
