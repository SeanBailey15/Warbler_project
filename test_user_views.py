"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Turn off SQL Echo for the tests, keeps test output in terminal less cluttered

app.config['SQLALCHEMY_ECHO'] = False

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        # Create two users to allow testing of certain features

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

        self.otheruser = User.signup(username="otheruser",
                                     email="other@test.com",
                                     password="otheruser",
                                     image_url=None)
        
        db.session.commit()

        # Create relationships between the two users

        self.testuser.following.append(self.otheruser)
        self.otheruser.following.append(self.testuser)
        db.session.commit()

        # Create an existing message for the testuser, and one for the otheruser

        msg1 = Message(text="This is a test", user_id=1)
        db.session.add(msg1)
        db.session.commit()

        msg2 = Message(text="Great job buddy!", user_id=2)
        db.session.add(msg2)
        db.session.commit()

    def tearDown(self):
        """Rollback session after bad transactions"""

        db.session.rollback() 

    def test_view_other_user_authenticated(self):
        """Can user view another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            otheruser = User.query.get_or_404(2)

            resp = c.get("/users/2")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(otheruser.username, html)

    def test_view_other_user_following_authenticated(self):
        """View who the otheruser is following"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            otheruser = User.query.get_or_404(2)

            # View who other user is following
            resp = c.get("/users/2/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(otheruser.following[0].username, 'testuser')
            self.assertIn(otheruser.following[0].username, html)

    def test_view_other_user_followers_authenticated(self):
        """View who the otheruser is being followed by"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            otheruser = User.query.get_or_404(2)

            # View who other user is following
            resp = c.get("/users/2/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(otheruser.followers[0].username, 'testuser')
            self.assertIn(otheruser.followers[0].username, html)

    def test_view_other_user_following_anon(self):
        """Are anonymous users prohibited from viewing who a user follows?"""

        with self.client as c:

            resp = c.get("/users/2/following")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_view_other_user_followers_anon(self):
        """Are anonymous users prohibited from viewing who is following a user?"""

        with self.client as c:

            resp = c.get("/users/2/followers")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")