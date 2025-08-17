from app import create_app


def test_docs_route_only_in_non_production():
    app_prod = create_app({"TESTING": True, "ENV": "production"})
    client_prod = app_prod.test_client()
    assert client_prod.get("/docs/").status_code == 404

    app_dev = create_app({"TESTING": True, "ENV": "development"})
    client_dev = app_dev.test_client()
    resp = client_dev.get("/docs/")
    assert resp.status_code == 302
