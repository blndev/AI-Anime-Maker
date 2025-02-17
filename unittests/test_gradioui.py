import unittest
import gradio as gr
from src.UI import AppState, wrap_handle_input_response, wrap_generate_image_response
from PIL import Image
import numpy as np

class TestGradioUI(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app_state = AppState(token=5)  # Initialize with 5 tokens
        self.test_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))  # Black test image

    def test_wrap_handle_input_response_success(self):
        """Test wrap_handle_input_response with successful case."""
        response = wrap_handle_input_response(
            app_state=self.app_state,
            start_enabled=True,
            image_description="Test description"
        )
        
        self.assertEqual(len(response), 5, "Response should contain 5 elements")
        self.assertEqual(response[0], gr.update(interactive=True), "Start button should be enabled")
        self.assertEqual(response[1], "Test description", "Description should match input")
        self.assertEqual(response[2], self.app_state.to_dict(), "AppState dict should be included")
        self.assertEqual(response[3], gr.update(visible=True), "Description area should be visible")
        self.assertEqual(response[4], self.app_state.token, "Token count should match AppState")

    def test_wrap_handle_input_response_disabled(self):
        """Test wrap_handle_input_response with disabled start button."""
        response = wrap_handle_input_response(
            app_state=self.app_state,
            start_enabled=False,
            image_description=""
        )
        
        self.assertEqual(response[0], gr.update(interactive=False), "Start button should be disabled")
        self.assertEqual(response[1], "", "Description should be empty")

    def test_wrap_generate_image_response_success(self):
        """Test wrap_generate_image_response with successful image generation."""
        response = wrap_generate_image_response(
            app_state=self.app_state,
            result_image=self.test_image
        )
        
        self.assertEqual(len(response), 4, "Response should contain 4 elements")
        self.assertEqual(response[0], self.test_image, "Result image should match input")
        self.assertEqual(response[1], self.app_state.to_dict(), "AppState dict should be included")
        self.assertEqual(response[2], gr.update(interactive=True), "Start button should be enabled with tokens > 0")
        self.assertEqual(response[3], self.app_state.token, "Token count should match AppState")

    def test_wrap_generate_image_response_no_tokens(self):
        """Test wrap_generate_image_response when no tokens are available."""
        self.app_state.token = 0  # Set tokens to 0
        response = wrap_generate_image_response(
            app_state=self.app_state,
            result_image=self.test_image
        )
        
        self.assertEqual(response[2], gr.update(interactive=False), "Start button should be disabled with no tokens")

    def test_wrap_generate_image_response_failed_generation(self):
        """Test wrap_generate_image_response when image generation fails."""
        response = wrap_generate_image_response(
            app_state=self.app_state,
            result_image=None
        )
        
        self.assertIsNone(response[0], "Result image should be None")
        self.assertEqual(response[2], gr.update(interactive=True), "Start button should still be enabled with tokens")

if __name__ == '__main__':
    unittest.main()
