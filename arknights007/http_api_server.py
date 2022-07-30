from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

from prts import daemon

app = Flask(__name__)
socketio = SocketIO(app)

sys_state_run = {
    'task': [True, True, True, True, True, True],
    'run': False,
}

log_buffer = []


def update_all_ui():
    emit('ui_update/update_sys_state', sys_state_run, broadcast=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/hello')
def hello_world():
    arg = request.args.get('arg')
    return f'arg={arg}, Hello World!'


#######################################################
# Log broadcast for PRTS


@socketio.on('log', namespace='/prts')
def on_log(data):
    print("receive log: ", data)
    socketio.emit('log', data, namespace='/socket', broadcast=True)
    log_buffer.append(data)
    if len(log_buffer) > 100:
        log_buffer.pop(0)


#######################################################
# UI Update

@socketio.on('ui_update/run', namespace='/socket')
def on_ui_update(message):
    print(message)
    sys_state_run['run'] = message['state']
    if message['state']:
        emit('log', '正在启动PRTS', namespace='/socket', broadcast=True)
        daemon.PRTSDaemon.run_all()
    else:
        emit('log', '正在强行终止PRTS', namespace='/socket', broadcast=True)
        daemon.PRTSDaemon.kill_process()
    update_all_ui()


@socketio.on('ui_update/tasks', namespace='/socket')
def on_ui_update(message):
    print(message)
    sys_state_run['task'][message['id']] = message['state']
    update_all_ui()


#######################################################
# WebSocket Connect/Disconnect

clients = set()
prts_client = set()


@socketio.on('connect', namespace='/prts')
def on_connect():
    prts_client.add(request.sid)
    print(f'{request.sid} PRTS主程序已连接, 当前PRTS连接数: {len(prts_client)}')
    emit('log', 'PRTS主程序已连接', namespace='/socket', broadcast=True)


@socketio.on('disconnect', namespace='/prts')
def on_disconnect():
    prts_client.remove(request.sid)
    print(f'{request.sid} PRTS主程序已断开, 当前PRTS连接数: {len(prts_client)}')
    sys_state_run['run'] = False
    update_all_ui()
    emit('log', 'PRTS主程序已断开连接', namespace='/socket', broadcast=True)


@socketio.on('connect', namespace='/socket')
def on_connect():
    # emit('my response', {'data': f'Connected sid={request.sid}'})
    clients.add(request.sid)
    print(f'{request.sid} 已连接, 当前连接数: {len(clients)}')
    # Update UI Control Info
    update_all_ui()
    for log_str in log_buffer:
        emit('log', log_str, room=request.sid)


@socketio.on('disconnect', namespace='/socket')
def on_disconnect():
    clients.remove(request.sid)
    print(f'{request.sid} 已断开, 当前连接数: {len(clients)}')


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    # socketio.run(app, host="0.0.0.0", port=8080)
    # logger.init(socketio) TODO: logger
    server = pywsgi.WSGIServer(('0.0.0.0', 9019), app, handler_class=WebSocketHandler)
    server.serve_forever()
