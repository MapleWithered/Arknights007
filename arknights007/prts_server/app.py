from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    arg = request.args.get('arg')
    return f'arg={arg}, Hello World!'



if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
