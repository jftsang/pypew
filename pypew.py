import os
import sys
import webbrowser
from threading import Thread
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, url_for, redirect, request
from jinja2 import StrictUndefined

import filters
import views
from utils import logger

load_dotenv()


class PyPew:
    def __init__(self):
        self.app: Optional[Flask] = None
        self.thread: Optional[Thread] = None


def create_app(pypew: Optional[PyPew] = None, **kwargs) -> Flask:
    # https://stackoverflow.com/a/50132788
    base_dir = '.'
    if hasattr(sys, '_MEIPASS'):
        base_dir = os.path.join(sys._MEIPASS)

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, 'static'),
        template_folder=os.path.join(base_dir, 'templates'),
        **kwargs
    )
    app.jinja_env.undefined = StrictUndefined

    app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME', 'localhost:5000')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'password')

    # store session information server-side to avoid large cookies
    # https://stackoverflow.com/questions/53551637/session-cookie-is-too-large-flask-application
    app.config['SESSION_TYPE'] = 'filesystem'

    app.add_url_rule(
        '/', 'index_view', views.index_view, methods=['GET', 'POST']
    )
    app.add_url_rule('/acknowledgements', 'acknowledgements_view', views.acknowledgements_view)
    app.add_url_rule('/feasts', 'feast_index_view', views.feast_index_view)
    app.add_url_rule('/feasts/api', 'feast_index_api', views.feast_index_api)
    app.add_url_rule('/feasts/api/upcoming', 'feast_upcoming_api', views.feast_upcoming_api)
    app.add_url_rule('/feast/<name>', 'feast_detail_view', views.feast_detail_view)
    app.add_url_rule('/feast/api/<name>', 'feast_detail_api', views.feast_detail_api)
    app.add_url_rule('/feast/api/<name>/date', 'feast_date_api', views.feast_date_api)
    app.add_url_rule('/feast/<name>/docx', 'feast_docx_view', views.feast_docx_view)
    app.add_url_rule('/feast/<name>/pdf', 'feast_pdf_view', views.feast_pdf_view)
    app.add_url_rule('/pewSheet/', 'pew_sheet_create_view', views.pew_sheet_create_view, methods=['GET'])
    app.add_url_rule('/pewSheet/docx', 'pew_sheet_docx_view', views.pew_sheet_docx_view, methods=['GET'])
    app.add_url_rule('/pewSheet/clearHistory',
                     'pew_sheet_clear_history_endpoint',
                     views.pew_sheet_clear_history_endpoint,
                     methods=['DELETE'])
    app.add_url_rule('/texts', 'texts_view', views.texts_view, methods=['GET', 'POST'])
    app.add_url_rule('/texts/csv', 'texts_download_csv_view', views.texts_download_csv_view)
    app.add_url_rule('/texts/xlsx', 'texts_download_xlsx_view', views.texts_download_xlsx_view)
    app.url_map.strict_slashes = False

    @app.before_request
    def clear_trailing_slashes():
        """https://stackoverflow.com/questions/40365390/trailing-slash-in-flask-route#40365514"""
        rp = request.path
        if rp != '/' and rp.endswith('/'):
            return redirect(rp[:-1])

    app.errorhandler(404)(views.not_found_handler)
    app.errorhandler(Exception)(views.internal_error_handler)

    for filter_name, filter_func in filters.filters_context.items():
        app.template_filter(filter_name)(filter_func)

    app.jinja_env.globals.update(len=len)

    if pypew is not None:
        pypew.app = app

    app.app_context().push()
    return app


def main(threaded: bool = False) -> None:
    """
    Start PyPew.
    :param threaded: If true, run the Flask app in a separate thread,
                     then open a webbrowser. Debug mode is not
                     available in this case.
    :return: None
    """
    pypew = PyPew()
    app = create_app(pypew)

    if threaded:
        logger.info('Starting Flask app thread...')
        # TODO use werkzeug server instead
        pypew.thread = Thread(
            target=lambda: app.run(debug=False, load_dotenv=True)
        )
        pypew.thread.start()
        logger.info('Started Flask app. Close this terminal window to terminate PyPew.')
        logger.info('Opening web browser...')
        with app.app_context():
            webbrowser.open(url_for('index_view'))
        pypew.thread.join()

    else:
        # noinspection FlaskDebugMode
        app.run(debug=True, load_dotenv=True)


if __name__ == '__main__':
    main(threaded=True)
