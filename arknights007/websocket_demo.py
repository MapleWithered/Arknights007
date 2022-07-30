from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
    <script src="https://cdn.bootcss.com/jquery/3.2.0/jquery.js"></script>
    <script src="https://cdn.socket.io/socket.io-3.0.5.js"></script>
</head>
<body>

    <div id="log"></div>

    <form id="emit">
        <input type="text" id="emit_data">
        <input type="submit" id="emit" value="aaa">
    </form>
    <form id="broadcast">
        <input type="text" id="broadcast_data">
        <input type="submit" id="broadcast" value="bbb">
    </form>

    <script>
           $(document).ready(function(){
                var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
                socket.on('my response', function(msg) {
                    $("#log").append('<p>Received: ' + msg.data + '</p>');
                });
                $('form#emit').submit(function(event) {
                    socket.emit('my event', {data: $('#emit_data').val()});
                    return false;
                });
                $('form#broadcast').submit(function(event) {
                    socket.emit('my broadcast event', {data: $('#broadcast_data').val()});
                    return false;
                });
            });
    </script>
    </body>
</html>
'''


@app.route('/')
def index():
    return html


@app.route('/hello')
def hello_world():
    arg = request.args.get('arg')
    return f'arg={arg}, Hello World!'


@socketio.on('my event', namespace='/test')
def test_message(message):
    print(1, message)
    emit('my response', {'data': message['data']})


@socketio.on('my broadcast event', namespace='/test')
def test_message(message):
    print(2, message)
    emit('my response', {'data': message['data']}, broadcast=True)


@socketio.on('connect', namespace='/test')
def test_connect():
    print(3)
    emit('my response', {'data': 'Connected'})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print(4)
    print('Client disconnected')


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    # socketio.run(app, host="0.0.0.0", port=8080)
    # logger.init(socketio) TODO: logger
    server = pywsgi.WSGIServer(('', 8080), app, handler_class=WebSocketHandler)
    server.serve_forever()