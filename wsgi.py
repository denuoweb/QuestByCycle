from gevent import monkey
monkey.patch_all()

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app)