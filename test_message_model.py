"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


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


class MessageModelTestCase(TestCase):
    """Test Message model and methods"""

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

        msg1 = Message(text= "Hi! My name is Bob!", user_id=1)
        msg2 = Message(text= "Hi Bob! I already saw your username, lol.", user_id=2)

        db.session.add_all([msg1, msg2])
        db.session.commit()

    def tearDown(self):
        """Rollback session after bad transactions"""

        db.session.rollback() 

    def test_message_model(self):
        """Test basic model functionality"""

        Bob = User.query.get_or_404(1)

        m = Message(
            text="Hello World", 
            user_id=Bob.id
            )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(Bob.messages), 2)
        self.assertIn("Hello World", Bob.messages[1].text)
        self.assertEqual(Bob.messages[1].id, 3)

    def test_likes(self):
        """Test the relationship between messages and user likes."""

        msg = Message.query.get_or_404(2)

        Bob = User.query.get_or_404(1)
        Jane = User.query.get_or_404(2)

        Bob.likes.append(msg)
        db.session.commit()

        self.assertEqual(len(Bob.likes), 1)
        self.assertIn('lol', Bob.likes[0].text)
        self.assertEqual(msg.user_id, Jane.id)
        self.assertNotEqual(msg.user_id, Bob.id)

        Bob.likes.remove(msg)
        db.session.commit()

        self.assertEqual(len(Bob.likes), 0)