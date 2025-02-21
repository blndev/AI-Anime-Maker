import unittest
import random, uuid, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.SessionState import SessionState

class TestGradioUISessionState(unittest.TestCase):
    def setUp(self):
        self.start = "1"

    def test_session_state_to_dict(self):
        """Test SessionState."""
        new_token = random.randint(1,50)
        new_session = str(uuid.uuid4())
        o1 = SessionState(new_token, new_session)
        o2 = SessionState()
        dct1 = o1.to_dict()
        dct2 = o2.to_dict()

        self.assertNotEqual(dct1["token"], dct2["token"])
        self.assertNotEqual(dct1["session"], dct2["session"])
        self.assertEqual(dct1["token"], new_token, "test that dict contains the token create in constructor")
        self.assertEqual(dct1["session"], new_session, "test that dict contains the session create in constructor")

        self.assertEqual(dct2["token"], 0, "test that dict has token=0 if not provided by constructor")
        self.assertIsNotNone(dct2["session"], "test that dict contains the session created in constructor")
        self.assertNotEqual(dct2["session"], "", "test that dict contains a session created in constructor")

        o1.token = new_token
        dct1 = o1.to_dict()
        self.assertEqual(o1.token, new_token)
        self.assertNotEqual(dct1["token"], dct2["token"])

    def test_session_state_from_dict(self):
        """Test SessionState."""
        new_token = random.randint(1,50)
        new_session = str(uuid.uuid4())
        dict1 = {
            "token": new_token,
            "session": new_session
        }

        o1 = SessionState.from_dict(dict1)
        o2 = SessionState()

        self.assertEqual(dict1["token"], o1.token)
        self.assertEqual(dict1["session"], o1.session)
        self.assertNotEqual(str(o1.token), str(o2.token), "test from dict will not influence new objects")
        self.assertNotEqual(str(o1.session), str(o2.session), "test from dict will not influence new objects")

    def test_session_state_to_dict_from_dict(self):
        """Test SessionState."""
        new_token = random.randint(1,50)
        new_session = str(uuid.uuid4())
        o1 = SessionState(token=new_token, session=new_session)
        dict1 = o1.to_dict()
        o2=SessionState.from_dict(dict1)
        
        self.assertEqual(o1.token, new_token)
        self.assertEqual(o1.session, new_session)
        self.assertEqual(o1.token, o2.token)
        self.assertEqual(o1.session, o2.session)

        #check that there is no link between the objects
        new_token = random.randint(1,50)
        new_session = str(uuid.uuid4())
        # chek link from o1 to o2
        o1.token = new_token
        o1.session = new_session
        self.assertEqual(o1.token, new_token)
        self.assertEqual(o1.session, new_session)
        self.assertNotEqual(o1.token, o2.token)
        self.assertNotEqual(o1.session, o2.session)

        # check link form o2 to o1
        new_token = random.randint(1,50)
        new_session = str(uuid.uuid4())
        o2.token = new_token
        o2.session = new_session
        self.assertEqual(o2.token, new_token)
        self.assertEqual(o2.session, new_session)
        self.assertNotEqual(o1.token, o2.token)
        self.assertNotEqual(o1.session, o2.session)

    def test_session_state_to_repr_and_back(self):
        """Test SessionState."""
        new_token = random.randint(1,50)
        new_session = str(uuid.uuid4())
        o1 = SessionState(token=new_token, session=new_session)
        s1 = repr(o1)
        t1 = str(o1)
        o2 = SessionState.from_gradio_state(s1)        
        self.assertEqual(o1.token, new_token)
        self.assertEqual(o1.session, new_session)
        self.assertEqual(o1.token, o2.token)
        self.assertEqual(o1.session, o2.session)


    def test_session_state_unique_sessionid(self):
        """Test SessionState."""
        o1 = SessionState()
        o2 = SessionState()
        self.assertNotEqual(str(o1.session), str(o2.session), "test init without session id")
        self.assertEqual(o1.token, 0, "test init without token value")
        self.assertEqual(o2.token, 0, "test init without token value")

        new_token = random.randint(1,50)
        # init with new token
        o3 = SessionState(new_token)
        self.assertEqual(o3.token, new_token, "test init with token value")
        self.assertNotEqual(str(o1.session), str(o3.session), "test init without session id")
        self.assertNotEqual(str(o2.session), str(o3.session), "test init without session id")


    def test_session_state_modify_token_values(self):
        """Test SessionState."""
        o1 = SessionState()
        o2 = SessionState()
        new_token = random.randint(1,50)
        o1.token = new_token
        self.assertEqual(o1.token, new_token, "test a changed token value")
        self.assertEqual(o2.token, 0, "changed token should not applied on second object")
    
    def test_session_state_modify_session_values(self):
        """Test SessionState."""
        o1 = SessionState()
        o2 = SessionState()
        new_session = str(uuid.uuid4())
        o1.session = new_session
        self.assertEqual(o1.session, new_session, "test change session value")
        self.assertNotEqual(o2.token, new_session, "changed session should not be applied on second object")
        