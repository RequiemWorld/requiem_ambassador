import os.path
import unittest
import tempfile
from requiem_ambassador.configuration import AmbassadorHTTPForwardOptions


class TestAmbassadorHTTPForwardOptionsConfigFileLoadingFunction(unittest.TestCase):

	def setUp(self):
		config_file_data = """
		[forwarding-http]
		main_api_base_url = http://main-api.example.com/main-api/
		main_cdn_base_url = http://main-cdn.example.com/cdn/
		image_cdn_base_url = http://image-cdn.example.com/image/
		game_image_cdn_base_url = http://game-image-cdn.example.com/image-game/
		cdn_dynamic_base_url = http://cdn-dynamic.example.com/cdn-dynamic/
		cdn_dynamic_common_base_url = http://cdn-dynamic-common.example.com/cdn-dynamic-common/
		"""
		self._temp_directory = tempfile.TemporaryDirectory()
		self._temp_file_path = os.path.join(self._temp_directory.name, "forward_options.cfg")
		with open(self._temp_file_path, "w") as f:
			f.write(config_file_data)

		self._loaded_config = AmbassadorHTTPForwardOptions.from_config_file(self._temp_file_path)

	def tearDown(self):
		self._temp_directory.cleanup()

	def test_should_read_main_api_base_url_from_section_in_config_file_correctly(self):
		self.assertEqual("http://main-api.example.com/main-api/", self._loaded_config.main_api_base_url)

	def test_should_read_main_cdn_base_url_from_section_in_config_file_correctly(self):
		self.assertEqual("http://main-cdn.example.com/cdn/", self._loaded_config.main_cdn_base_url)

	def test_should_read_image_cdn_base_url_from_section_in_config_file_correctly(self):
		self.assertEqual("http://image-cdn.example.com/image/", self._loaded_config.image_cdn_base_url)

	def test_should_read_game_image_cdn_base_url_from_section_in_config_file_correctly(self):
		self.assertEqual("http://game-image-cdn.example.com/image/", self._loaded_config.game_image_cdn_base_url)

	def test_should_read_dynamic_cdn_base_url_from_section_in_config_file_correctly(self):
		self.assertEqual("http://cdn-dynamic.example.com/cdn-dynamic/", self._loaded_config.cdn_dynamic_base_url)

	def test_should_read_dynamic_cdn_common_base_url_from_section_in_config_file_correctly(self):
		self.assertEqual("http://cdn-dynamic-common.example.com/cdn-dynamic-common/", self._loaded_config.cdn_dynamic_common_url)