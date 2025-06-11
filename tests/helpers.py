from flask import url_for

def url_for_path(app, *args, **kwargs):
    """Generate a URL path using a temporary request context."""
    with app.test_request_context():
        return url_for(*args, **kwargs)
