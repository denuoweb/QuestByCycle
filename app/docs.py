import os

from flask import Blueprint, current_app, send_from_directory
from flask_login import login_required


docs_bp = Blueprint("docs", __name__, url_prefix="/docs")


@docs_bp.route("/openapi.yaml")
@login_required
def openapi_yaml():
    """Return the OpenAPI specification."""
    docs_path = os.path.join(current_app.root_path, "..", "docs")
    return send_from_directory(docs_path, "openapi.yaml")


@docs_bp.route("/")
@login_required
def redoc():
    """Serve the Redoc API documentation."""
    return (
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>API Docs</title>
            <script
                src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"
                integrity="sha384-4vOjrBu7SuDWXcAw1qFznVLA/sKL+0l4nn+J1HY8w7cpa6twQEYuh4b0Cwuo7CyX"
                crossorigin="anonymous"
            ></script>
        </head>
        <body>
            <redoc spec-url="/docs/openapi.yaml"></redoc>
        </body>
        </html>
        """,
        200,
        {"Content-Type": "text/html"},
    )
