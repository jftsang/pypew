from pypew import create_app, PyPew

app = create_app(PyPew())

if __name__ == '__main__':
    app.run()
