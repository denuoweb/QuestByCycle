from unittest.mock import patch

from app import create_app


def test_generate_demo_game_called(monkeypatch):
    with patch('app.generate_demo_game') as mock_gen, \
         patch('app.init_queue') as mock_init_queue, \
         patch('app.admin.create_super_admin'):
        create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        mock_gen.assert_called_once()
