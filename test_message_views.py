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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

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

        msg = Message(text="This is a test", user_id=1)
        db.session.add(msg)
        db.session.commit()

        msg2 = Message(text="Great job buddy!", user_id=2)
        db.session.add(msg2)
        db.session.commit()

    def tearDown(self):
        """Rollback session after bad transactions"""

        db.session.rollback() 

    def test_add_message_authenticated(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.get(3)
            self.assertEqual(msg.text, "Hello")

    def test_redirect_delete_message_authenticated(self):
        """Make sure user gets redirected"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/1/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/users/1')        

    def test_delete_message_authenticated(self):
        """Can user delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message.query.get_or_404(1)

            resp = c.post("/messages/1/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(msg.text, html)

    def test_add_message_anon(self):
        """Are anonymous users prohibited from adding messages?"""

        with self.client as c:

            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_delete_message_anon(self):
        """Are anonymous users prohibited from deleting messages?"""

        with self.client as c:

            resp = c.post("/messages/1/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")