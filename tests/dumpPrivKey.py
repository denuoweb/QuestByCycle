from app import create_app
from app.models.user import User
app = create_app()
with app.app_context():
    user = User.query.filter_by(username='t12').first()
    with open('actor_priv.pem','w') as f:
        f.write(user.private_key)