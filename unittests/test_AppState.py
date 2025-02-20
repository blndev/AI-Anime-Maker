import unittest
from src.UI import (AppState)
import random, uuid

class TestGradioUIAppState(unittest.TestCase):
    def setUp(self):
        self.start = "1"

    def test_app_state_to_dict(self):
        """Test wrap_handle_input_response with disabled start button."""
        new_token = random.randint(1,50)
        new_session = uuid.uuid4()
        o1 = AppState(new_token, new_session)
        o2 = AppState()
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

    def test_app_state_from_dict(self):
        """Test wrap_handle_input_response with disabled start button."""
        new_token = random.randint(1,50)
        new_session = uuid.uuid4()
        dict1 = {
            "token": new_token,
            "session": new_session
        }

        o1 = AppState.from_dict(dict1)
        o2 = AppState()

        self.assertEqual(dict1["token"], o1.token)
        self.assertEqual(dict1["session"], o1.session)
        self.assertNotEqual(str(o1.token), str(o2.token), "test from dict will not influence new objects")
        self.assertNotEqual(str(o1.session), str(o2.session), "test from dict will not influence new objects")

    def test_app_state_to_dict_from_dict(self):
        """Test wrap_handle_input_response with disabled start button."""
        new_token = random.randint(1,50)
        new_session = uuid.uuid4()
        o1 = AppState(token=new_token, session=new_session)
        dict1 = o1.to_dict()
        o2=AppState.from_dict(dict1)
        
        self.assertEqual(o1.token, new_token)
        self.assertEqual(o1.session, new_session)
        self.assertEqual(o1.token, o2.token)
        self.assertEqual(o1.session, o2.session)

        #check that there is no link between the objects
        new_token = random.randint(1,50)
        new_session = uuid.uuid4()
        # chek link from o1 to o2
        o1.token = new_token
        o1.session = new_session
        self.assertEqual(o1.token, new_token)
        self.assertEqual(o1.session, new_session)
        self.assertNotEqual(o1.token, o2.token)
        self.assertNotEqual(o1.session, o2.session)

        # check link form o2 to o1
        new_token = random.randint(1,50)
        new_session = uuid.uuid4()
        o2.token = new_token
        o2.session = new_session
        self.assertEqual(o2.token, new_token)
        self.assertEqual(o2.session, new_session)
        self.assertNotEqual(o1.token, o2.token)
        self.assertNotEqual(o1.session, o2.session)



    def test_app_state_creation_unique_identifer(self):
        """Test wrap_handle_input_response with disabled start button."""
        o1 = AppState()
        o2 = AppState()
        self.assertNotEqual(str(o1.session), str(o2.session), "test init without session id")
        self.assertEqual(o1.token, 0, "test init without token value")
        self.assertEqual(o2.token, 0, "test init without token value")

        new_token = random.randint(1,50)
        # init with new token
        o3 = AppState(new_token)
        self.assertEqual(o3.token, new_token, "test init with token value")

    def test_app_state_modify_token_values(self):
        """Test wrap_handle_input_response with disabled start button."""
        o1 = AppState()
        o2 = AppState()
        new_token = random.randint(1,50)
        o1.token = new_token
        self.assertEqual(o1.token, new_token, "test a changed token value")
        self.assertEqual(o2.token, 0, "changed token should not applied on second object")
    
    def test_app_state_modify_session_values(self):
        """Test wrap_handle_input_response with disabled start button."""
        o1 = AppState()
        o2 = AppState()
        new_session = uuid.uuid4()
        o1.session = new_session
        self.assertEqual(o1.session, new_session, "test change session value")
        self.assertNotEqual(o2.token, new_session, "changed session should not be applied on second object")
        