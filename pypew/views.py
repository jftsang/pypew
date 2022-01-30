from tempfile import NamedTemporaryFile

from flask import render_template, flash, send_file, Response

from pypew.forms import MyForm
from pypew.models import Service, Extract


def index_view():
    form = MyForm()
    if form.validate_on_submit():
        flash(f"Hello, {form.name.data}, you selected "
              f"{form.selectable_one.data} and {form.selectable_two.data} "
              f"and option {form.radio.data}")

    return render_template('index.html', nav_active='Home', form=form)


def service_index_view(**kwargs):
    services = Service.all()
    return render_template(
        'services.html', nav_active='Services', services=services, **kwargs
    )


def service_view(name):
    try:
        service = Service.get(name=name)
    except Service.NotFoundError:
        flash(f'Service {name} not found.')
        return service_index_view(status=404)

    return render_template('pewsheet.html', service=service, Extract=Extract)



def service_docx_view(name):
    try:
        service = Service.get(name=name)
    except Service.NotFoundError:
        flash(f'Service {name} not found.')
        return service_index_view(status=404)

    with NamedTemporaryFile(suffix=".docx", prefix=name) as tf:
        ...
        return send_file(tf.name)
