from rq import Worker

from app import create_app
from app.tasks import init_queue


def main() -> None:
    app = create_app()
    queue = init_queue(app)
    # push the Flask context so tasks can use current_app, etc.
    app.app_context().push()

    # create a Worker bound to this queue and its connection
    worker = Worker([queue], connection=queue.connection)
    worker.work()


if __name__ == "__main__":
    main()
