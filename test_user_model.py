"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

# Turn off SQL Echo for the tests, keeps test output in terminal less cluttered

app.config['SQLALCHEMY_ECHO'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# db.drop_all()
# db.create_all()

# *** STUDENT HERE! DECIDED I DID NOT LIKE THIS APPROACH AS IN EACH SUCCESSIVE TEST
# THE USER IDS WOULD INCREMENT. I DECIDED IT WAS BEST TO DROP THEN CREATE THE TABLES
# PER TEST, KEEPING USER IDS CONSTANT. ***

class UserModelTestCase(TestCase):
    """Test User model and methods"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        Bob = User.signup(
            username = 'Bob',
            email = 'bob@email.com',
            password = 'BobIsCool',
            image_url = '/static/images/default-pic.png'
        )

        Jane = User.signup(
            username = 'JaneSmith',
            email = 'jsmith@email.com',
            password = 'janey6465',
            image_url = '/static/images/default-pic.png'
        )

        db.session.add_all([Bob, Jane])
        db.session.commit()

    def tearDown(self):
        """Rollback session after bad transactions"""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_signup(self):
        """Does the signup method work correctly?
        Users created via User.signup() in setUp should be accessible.
        Does the user password get hashed?
        """

        Bob = User.query.get_or_404(1)
        Jane = User.query.get_or_404(2)

        self.assertEqual(Bob.username, 'Bob')
        self.assertEqual(Bob.email, 'bob@email.com')
        self.assertIn('$2b$12$', Bob.password)

        self.assertEqual(Jane.username, 'JaneSmith')
        self.assertEqual(Jane.email, 'jsmith@email.com')
        self.assertIn('$2b$12$', Jane.password)

    def test_user_authentication(self):
        """Should return a user when proper credentials are given."""

        self.assertEqual(User.query.get(1), User.authenticate('Bob', 'BobIsCool'))
        self.assertEqual(User.query.get(2), User.authenticate('JaneSmith', 'janey6465'))

    def test_user_is_following(self):
        """Test if is_following method successfully detects
        whether one user is following another, or not.
        """

        Bob = User.query.get_or_404(1)
        Jane = User.query.get_or_404(2)

        Bob.following.append(Jane)
        db.session.commit()

        self.assertEqual(Bob.is_following(Jane), True)
        self.assertEqual(Jane.is_following(Bob), False)
        self.assertEqual(len(Jane.followers), 1)

        Bob.following.remove(Jane)
        db.session.commit()

        self.assertEqual(Bob.is_following(Jane), False)
        self.assertEqual(len(Jane.followers), 0)

    def test_user_is_followed_by(self):
        """Test if is_followed_by method successfully detects
        whether one user is followed by another, or not
        """

        Bob = User.query.get_or_404(1)
        Jane = User.query.get_or_404(2)

        Bob.following.append(Jane)
        db.session.commit() 

        self.assertEqual(Jane.is_followed_by(Bob), True)       
        self.assertEqual(Bob.is_followed_by(Jane), False)
        self.assertEqual(len(Jane.followers), 1)

        Bob.following.remove(Jane)
        db.session.commit()

        self.assertEqual(Jane.is_followed_by(Bob), False)
        self.assertEqual(len(Jane.followers), 0)