from flask import render_template, flash

from pypew.forms import MyForm
from pypew.models import Service, Extract


def index_view():
    form = MyForm()
    if form.validate_on_submit():
        flash(f"Hello, {form.name.data}, you selected "
              f"{form.selectable_one.data} and {form.selectable_two.data} "
              f"and option {form.radio.data}")

    return render_template('index.html', nav_active='Home', form=form)


def service_index_view():
    services = Service.all()
    return render_template(
        'services.html', nav_active='Services', services=services
    )


def service_view(name):
    service = Service.get(name=name)
    for e in service['elements']:
        if 'Reading' in e:
            text = Extract.get(name=service['elements'][e]).text
            service['elements'][e] = text

    return render_template('pewsheet.html', service=service)
