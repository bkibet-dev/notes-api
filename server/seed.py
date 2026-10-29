"""Populate the database with example users and notes.

Run from the server/ directory:  python seed.py
WARNING: this deletes all existing users and notes first.
"""
from random import randint

from faker import Faker

from app import app
from extensions import db
from models import Note, User

fake = Faker()
Faker.seed(42)

SEED_PASSWORD = "password123"

# alice has enough notes to exercise pagination (default page size is 10).
USERS = {"alice": 25, "bob": 8, "carol": 3}


def seed():
    with app.app_context():
        print("Clearing existing data...")
        Note.query.delete()
        User.query.delete()

        for username, note_count in USERS.items():
            user = User(username=username)
            user.password_hash = SEED_PASSWORD
            db.session.add(user)
            db.session.flush()  # assigns user.id

            for _ in range(note_count):
                db.session.add(
                    Note(
                        title=fake.sentence(nb_words=randint(3, 6)).rstrip("."),
                        content="\n\n".join(fake.paragraphs(nb=randint(1, 3))),
                        user_id=user.id,
                    )
                )

        db.session.commit()
        print(f"Seeded {len(USERS)} users (password: {SEED_PASSWORD}) and "
              f"{sum(USERS.values())} notes.")


if __name__ == "__main__":
    seed()
