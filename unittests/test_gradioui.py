import unittest
from unittest.mock import patch, MagicMock
import gradio as gr
from src.UI import (
    SessionState,
    wrap_handle_input_response,
    wrap_generate_image_response,
    action_handle_input_file,
    action_generate_image
)
from PIL import Image
import numpy as np
import src.config as config
from hashlib import sha1
from datetime import datetime, timedelta

class TestGradioUI(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.session_state = SessionState(token=5)  # Initialize with 5 tokens
        self.test_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))  # Black test image

    def test_wrap_handle_input_response_success(self):
        """Test wrap_handle_input_response with successful case."""
        response = wrap_handle_input_response(
            session_state=self.session_state,
            start_enabled=True,
            image_description="Test description"
        )
        
        self.assertEqual(len(response), 5, "Response should contain 5 elements")
        self.assertEqual(response[0], gr.update(interactive=True), "Start button should be enabled")
        self.assertEqual(response[1], "Test description", "Description should match input")
        self.assertEqual(response[2], self.session_state, "AppState dict should be included")
        self.assertEqual(response[3], gr.update(visible=True), "Description area should be visible")
        self.assertEqual(response[4], self.session_state.token, "Token count should match AppState")

    def test_wrap_handle_input_response_disabled(self):
        """Test wrap_handle_input_response with disabled start button."""
        response = wrap_handle_input_response(
            session_state=self.session_state,
            start_enabled=False,
            image_description=""
        )
        
        self.assertEqual(response[0], gr.update(interactive=False), "Start button should be disabled")
        self.assertEqual(response[1], "", "Description should be empty")

    def test_wrap_generate_image_response_success(self):
        """Test wrap_generate_image_response with successful image generation."""
        response = wrap_generate_image_response(
            session_state=self.session_state,
            result_image=self.test_image
        )
        
        self.assertEqual(len(response), 4, "Response should contain 4 elements")
        self.assertEqual(response[0], self.test_image, "Result image should match input")
        self.assertEqual(response[1], self.session_state, "AppState dict should be included")
        self.assertEqual(response[2], gr.update(interactive=True), "Start button should be enabled with tokens > 0")
        self.assertEqual(response[3], self.session_state.token, "Token count should match AppState")

    def test_wrap_generate_image_response_no_tokens(self):
        """Test wrap_generate_image_response when no tokens are available."""
        self.session_state.token = 0  # Set tokens to 0
        response = wrap_generate_image_response(
            session_state=self.session_state,
            result_image=self.test_image
        )
        
        self.assertEqual(response[2], gr.update(interactive=False), "Start button should be disabled with no tokens")

    def test_wrap_generate_image_response_failed_generation(self):
        """Test wrap_generate_image_response when image generation fails."""
        response = wrap_generate_image_response(
            session_state=self.session_state,
            result_image=None
        )
        
        self.assertIsNone(response[0], "Result image should be None")
        self.assertEqual(response[2], gr.update(interactive=True), "Start button should still be enabled with tokens")

class TestActionHandleInputFile(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        from src.UI import session_image_hashes
        session_image_hashes.clear()  # Clear shared state
        self.session_state = SessionState(token=5)
        self.test_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        self.mock_request = MagicMock()
        self.mock_request.session_hash = "test_session"
        self.mock_request.client.host = "127.0.0.1"
        self.mock_request.headers = {
            "user-agent": "test-browser",
            "accept-language": "en-US"
        }

    def tearDown(self):
        """Clean up after each test method."""
        from src.UI import session_image_hashes
        session_image_hashes.clear()  # Clear shared state

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    def test_handle_input_no_image(self, mock_analytics, mock_config):
        """Test handling when no image is provided."""
        response = action_handle_input_file(self.mock_request, None, self.session_state)
        self.assertEqual(response[0], gr.update(interactive=False))
        self.assertEqual(response[1], "")

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    def test_handle_input_no_request(self, mock_analytics, mock_config):
        """Test handling when no request object is provided (API usage)."""
        response = action_handle_input_file(None, self.test_image, self.session_state)
        self.assertEqual(response[0], gr.update(interactive=False))

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.action_describe_image')
    def test_handle_input_with_analytics(self, mock_describe, mock_analytics, mock_config):
        """Test handling with analytics enabled."""
        mock_config.is_analytics_enabled.return_value = True
        mock_config.is_feature_generation_with_token_enabled.return_value = False
        mock_describe.return_value = "Test description"

        response = action_handle_input_file(self.mock_request, self.test_image, self.session_state)
        
        mock_analytics.save_input_image_details.assert_called_once()
        self.assertEqual(response[1], "Test description")

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.action_describe_image')
    @patch('src.UI.analyze_faces')
    def test_handle_input_with_tokens(self, mock_faces, mock_describe, mock_analytics, mock_config):
        """Test handling with token generation enabled."""
        # Configure mock returns
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.get_token_for_new_image.return_value = 1
        mock_config.get_token_bonus_for_face.return_value = 2
        mock_config.get_token_time_lock_for_new_image.return_value = 60  # 60 minutes lock
        mock_config.get_token_bonus_for_smile.return_value = 1
        mock_config.get_token_bonus_for_cuteness.return_value = 1
        mock_describe.return_value = "Test description"
        mock_faces.return_value = [{"isFemale": True, "maxAge": 25, "minAge": 20}]

        response = action_handle_input_file(self.mock_request, self.test_image, self.session_state)
        
        session_state_dict = response[2]
        reconstructed_state = session_state_dict
        self.assertGreater(reconstructed_state.token, self.session_state.token)

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.action_describe_image')
    @patch('src.UI.analyze_faces')
    def test_handle_input_duplicate_image(self, mock_faces, mock_describe, mock_analytics, mock_config):
        """Test handling when the same image is uploaded twice within the lock period."""
        # Configure mock returns
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.get_token_for_new_image.return_value = 1
        mock_config.get_token_time_lock_for_new_image.return_value = 60  # 60 minutes lock
        mock_describe.return_value = "Test description"
        mock_faces.return_value = []

        # First upload
        response1 = action_handle_input_file(self.mock_request, self.test_image, self.session_state)
        session_state_dict1 = response1[2]
        state_after_first = SessionState.from_gradio_state(session_state_dict1)
        
        # Second upload of same image
        response2 = action_handle_input_file(self.mock_request, self.test_image, state_after_first)
        session_state_dict2 = response2[2]
        state_after_second = SessionState.from_gradio_state(session_state_dict2)
        
        # Token count should not increase on second upload
        self.assertEqual(state_after_first.token, state_after_second.token)

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.action_describe_image')
    def test_handle_input_description_error(self, mock_describe, mock_analytics, mock_config):
        """Test handling when image description fails."""
        mock_describe.side_effect = Exception("Description failed")
        mock_config.is_feature_generation_with_token_enabled.return_value = False

        response = action_handle_input_file(self.mock_request, self.test_image, self.session_state)
        
        self.assertEqual(response[1], "")  # Description should be empty on error

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.action_describe_image')
    @patch('src.UI.analyze_faces')
    def test_handle_input_expired_lock(self, mock_faces, mock_describe, mock_analytics, mock_config):
        """Test handling when the same image is uploaded after the lock period expires."""
        from datetime import datetime, timedelta
        # Configure mock returns
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.get_token_for_new_image.return_value = 1
        mock_config.get_token_time_lock_for_new_image.return_value = 60  # 60 minutes lock
        mock_describe.return_value = "Test description"
        mock_faces.return_value = []

        # First upload
        response1 = action_handle_input_file(self.mock_request, self.test_image, self.session_state)
        session_state_dict1 = response1[2]
        state_after_first = session_state_dict1
        
        # Simulate time passing - modify the timestamp in session_image_hashes
        from src.UI import session_image_hashes
        image_sha1 = sha1(self.test_image.tobytes()).hexdigest()
        if image_sha1 in session_image_hashes:
            session_image_hashes[image_sha1] = datetime.now() - timedelta(minutes=61)  # Past the lock period
        
        # Second upload of same image
        response2 = action_handle_input_file(self.mock_request, self.test_image, state_after_first)
        session_state_dict2 = response2[2]
        state_after_second = SessionState.from_gradio_state(session_state_dict2)
        
        # Token count should increase on second upload since lock expired
        self.assertGreater(state_after_second.token, state_after_first.token)

class TestActionGenerateImage(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        from src.UI import session_image_hashes
        session_image_hashes.clear()  # Clear shared state
        self.session_state = SessionState(token=5)
        self.test_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        self.mock_request = MagicMock()
        self.mock_request.client.host = "127.0.0.1"
        self.style = "Anime Style"
        self.strength = 0.75
        self.steps = 20
        self.image_description = "Test description"

    def tearDown(self):
        """Clean up after each test method."""
        from src.UI import session_image_hashes
        session_image_hashes.clear()  # Clear shared state

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.AI')
    def test_generate_image_tokens_disabled(self, mock_ai, mock_analytics, mock_config):
        """Test image generation when tokens are disabled."""
        # Configure all token-related mocks
        mock_config.is_feature_generation_with_token_enabled.return_value = False
        mock_config.SKIP_AI = False
        mock_config.get_token_for_new_image.return_value = 0
        mock_config.get_token_bonus_for_face.return_value = 0
        mock_config.get_token_bonus_for_smile.return_value = 0
        mock_config.get_token_bonus_for_cuteness.return_value = 0
        mock_ai.generate_image.return_value = self.test_image
        mock_ai.describe_image.return_value = self.image_description

        response = action_generate_image(
            self.mock_request,
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        self.assertEqual(response[0], self.test_image)  # Result image
        reconstructed_state = response[1]
        self.assertEqual(reconstructed_state.token, 9)  # Token is always set to 10 and decrement by one for each tunr if taken handling is disabled

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.AI')
    def test_generate_image_success(self, mock_ai, mock_analytics, mock_config):
        """Test successful image generation."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.SKIP_AI = False
        mock_ai.generate_image.return_value = self.test_image
        mock_ai.describe_image.return_value = self.image_description

        response = action_generate_image(
            self.mock_request,
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        self.assertEqual(response[0], self.test_image)  # Result image
        reconstructed_state = response[1]
        self.assertEqual(reconstructed_state.token, self.session_state.token - 1)  # Token decremented

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    def test_generate_image_no_tokens(self, mock_analytics, mock_config):
        """Test generation attempt with no tokens."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        self.session_state.token = 0

        response = action_generate_image(
            self.mock_request,
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        self.assertEqual(response[0], self.test_image)  # Original image returned
        reconstructed_state = response[1]
        self.assertEqual(reconstructed_state.token, 0)  # Token remains 0

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.AI')
    def test_generate_image_no_description(self, mock_ai, mock_analytics, mock_config):
        """Test generation with missing description."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.SKIP_AI = False
        mock_ai.describe_image.return_value = "AI generated description"
        mock_ai.generate_image.return_value = self.test_image

        response = action_generate_image(
            self.mock_request,
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            None,  # No description
            self.session_state
        )

        mock_ai.describe_image.assert_called_once()
        self.assertEqual(response[0], self.test_image)

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.AI')
    def test_generate_image_runtime_error(self, mock_ai, mock_analytics, mock_config):
        """Test handling of runtime errors during generation."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.SKIP_AI = False
        mock_ai.generate_image.side_effect = RuntimeError("Generation failed")

        response = action_generate_image(
            self.mock_request,
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        self.assertIsNone(response[0])  # No image returned
        reconstructed_state = response[1]
        self.assertEqual(reconstructed_state.token, self.session_state.token)  # Token not decremented on error

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.utils')
    def test_generate_image_skip_ai(self, mock_utils, mock_analytics, mock_config):
        """Test image generation when AI is skipped."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.SKIP_AI = True
        mock_utils.image_convert_to_sepia.return_value = self.test_image

        response = action_generate_image(
            self.mock_request,
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        mock_utils.image_convert_to_sepia.assert_called_once()
        self.assertEqual(response[0], self.test_image)

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    def test_generate_image_no_input_image(self, mock_analytics, mock_config):
        """Test generation attempt with no input image."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True

        response = action_generate_image(
            self.mock_request,
            None,  # No input image
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        self.assertIsNone(response[0])  # No result image
        reconstructed_state = response[1]
        self.assertEqual(reconstructed_state.token, self.session_state.token)  # Token not decremented

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    def test_generate_image_no_request(self, mock_analytics, mock_config):
        """Test generation attempt with no request object."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True

        response = action_generate_image(
            None,  # No request object
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        self.assertIsNone(response[0])  # No result image
        reconstructed_state = response[1]
        self.assertEqual(reconstructed_state.token, self.session_state.token)  # Token not decremented

    @patch('src.UI.config')
    @patch('src.UI.analytics')
    @patch('src.UI.AI')
    def test_generate_image_with_analytics(self, mock_ai, mock_analytics, mock_config):
        """Test image generation with analytics enabled."""
        mock_config.is_feature_generation_with_token_enabled.return_value = True
        mock_config.is_analytics_enabled.return_value = True
        mock_config.SKIP_AI = False
        mock_ai.generate_image.return_value = self.test_image

        response = action_generate_image(
            self.mock_request,
            self.test_image,
            self.style,
            self.strength,
            self.steps,
            self.image_description,
            self.session_state
        )

        mock_analytics.save_generation_details.assert_called_once()
        self.assertEqual(response[0], self.test_image)

if __name__ == '__main__':
    unittest.main()
