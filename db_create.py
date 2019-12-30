from app import db
from app.models import User, History

# drop all of the existing database tables
db.drop_all()

# create the database and the database table
db.create_all()
user = User(email="admin@example.com", firstname="John",
            lastname="Doe", gender="Male", profession="Radiologist")
user.set_password("")
db.session.add(user)
db.session.commit()

# commit the changes
db.session.commit()
