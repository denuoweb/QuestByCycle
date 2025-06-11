from rq import Worker, Connection

from app import create_app
from app.tasks import init_queue


def main() -> None:
    app = create_app()
    queue = init_queue(app)
    app.app_context().push()

    with Connection(queue.connection):
        worker = Worker([queue])
        worker.work()


if __name__ == "__main__":
    main()
