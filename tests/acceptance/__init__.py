import os
import shutil
import sys
import signal
import tempfile
import httpx
import subprocess
from dataclasses import dataclass
from subprocess import Popen
from unittest import IsolatedAsyncioTestCase
from ._infrastructure import pick_random_available_port
from ._infrastructure import pick_random_loopback_address
from ._infrastructure import wait_for_port_connectivity


def _get_path_relative_to_file(path: str) -> str:
	return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

@dataclass(frozen=True)
class _AmbassadorTestingConfigInfo:
	main_api_base_url: str
	main_cdn_base_url: str
	image_cdn_base_url: str
	game_image_cdn_base_url: str
	cdn_dynamic_base_url: str
	cdn_dynamic_common_base_url: str

	main_api_base_path: str
	main_cdn_base_path: str
	image_cdn_base_path: str
	game_image_cdn_base_path: str
	cdn_dynamic_base_path: str
	cdn_dynamic_common_base_path: str

	@classmethod
	def from_same_base_url_for_each(cls, every_base_url: str) -> "_AmbassadorTestingConfigInfo":
		main_api_base_path = "/main-api/"
		main_cdn_base_path = "/main-cdn/"
		image_cdn_base_path = "/image-cdn/"
		game_image_cdn_base_path = "/game-image-cdn/"
		cdn_dynamic_base_path = "/cdn-dynamic-image/"
		cdn_dynamic_common_base_path = "/cdn-dynamic-common/"

		testing_config_info = _AmbassadorTestingConfigInfo(
			main_api_base_path=main_api_base_path,
			main_cdn_base_path=main_cdn_base_path,
			image_cdn_base_path=image_cdn_base_path,
			game_image_cdn_base_path=game_image_cdn_base_path,
			cdn_dynamic_base_path=cdn_dynamic_base_path,
			cdn_dynamic_common_base_path=cdn_dynamic_common_base_path,
			main_api_base_url=f"{every_base_url}/{main_api_base_path}",
			main_cdn_base_url=f"{every_base_url}/{main_cdn_base_path}",
			image_cdn_base_url=f"{every_base_url}/{image_cdn_base_path}",
			game_image_cdn_base_url=f"{every_base_url}/{game_image_cdn_base_path}",
			cdn_dynamic_base_url=f"{every_base_url}/{cdn_dynamic_base_path}",
			cdn_dynamic_common_base_url=f"{every_base_url}/{cdn_dynamic_common_base_path}")
		return testing_config_info

	def to_config_file_string(self, http_host: str, http_port: int, game_host: str, game_port: int) -> str:
		testing_config_info = self
		config_string = f"""
		[listening]
		http_proxy_host = {http_host}
		http_proxy_port = {http_port}
		game_proxy_host = {game_host}
		game_proxy_port = {game_port}

		[forwarding]
		upstream_game_websocket = http://example.com/game_server.ws

		[forwarding-http]
		main_api_base_url = {testing_config_info.main_api_base_url}
		main_cdn_base_url = {testing_config_info.main_cdn_base_url}
		image_cdn_base_url = {testing_config_info.image_cdn_base_url}
		game_image_cdn_base_url = {testing_config_info.game_image_cdn_base_url}
		cdn_dynamic_base_url = {testing_config_info.cdn_dynamic_base_url}
		cdn_dynamic_common_base_url = {testing_config_info.cdn_dynamic_common_base_url}
		"""
		return config_string

def _make_ambassador_testing_config(every_cdn_base_url: str) -> _AmbassadorTestingConfigInfo:
	"""
	:param every_cdn_base_url: The base URL to use for every single CDN option. For testing we'll just switch the paths up between them.
	"""
	assert every_cdn_base_url.startswith("http")
	assert not every_cdn_base_url.endswith("/")
	return _AmbassadorTestingConfigInfo.from_same_base_url_for_each(every_cdn_base_url)

def _place_files_in_directory_for_testing(
		ambassador_script_path: str,
		ambassador_package_path: str,
		destination_directory_path: str,
		destination_script_name: str,
		destination_config_name: str,
		destination_config_string: str) -> None:
	assert not ambassador_package_path.endswith("/")
	ambassador_package_directory_name = os.path.basename(ambassador_package_path)
	destination_script_path = os.path.join(destination_directory_path, destination_script_name)
	destination_config_path = os.path.join(destination_directory_path, destination_config_name)
	destination_package_path = os.path.join(destination_directory_path, ambassador_package_directory_name)
	shutil.copy(ambassador_script_path, destination_script_path)
	shutil.copytree(ambassador_package_path, destination_package_path)
	with open(destination_config_path, "w") as f:
		f.write(destination_config_string)


def _write_ambassador_config_to_directory(ambassador_config: str, directory_path: str, file_name: str) -> None:
	destination_path = os.path.join(directory_path, file_name)
	with open(destination_path, "w") as f:
		f.write(ambassador_config)


def _start_application_and_wait_for_port_availability(
		python_path: str,
		ambassador_path: str,
		game_host: str,
		game_port: int,
		http_host: str,
		http_port: int) -> Popen:
	"""
	:raises TimeoutError: Will raise timeout and kill the process when attempts to connect to either port fail.
	"""
	ambassador_parent_directory = os.path.dirname(ambassador_path)
	process = subprocess.Popen([python_path, ambassador_path], cwd=ambassador_parent_directory)
	try:
		wait_for_port_connectivity(game_host, game_port, 3)
		wait_for_port_connectivity(http_host, http_port, 3)
	except TimeoutError as exception:
		# Won't kill grand children, but we shouldn't be forking in this implementation, so this isn't a problem
		process.send_signal(signal.SIGTERM)
		raise exception
	return process


class AmbassadorAcceptanceTestCase(IsolatedAsyncioTestCase):

	async def asyncSetUp(self):
		self.chosen_loopback_address = pick_random_loopback_address()
		self.chosen_game_proxy_port = pick_random_available_port(for_address=self.chosen_loopback_address)
		self.chosen_http_proxy_port = pick_random_available_port(for_address=self.chosen_loopback_address)
		self._temp_directory = tempfile.TemporaryDirectory()
		self._temp_directory_path = self._temp_directory.name
		testing_config = _make_ambassador_testing_config(
			every_cdn_base_url="http://example.com",  # this is for development/exploratory testing of this class
		)
		ambassador_config_string = testing_config.to_config_file_string(
			game_host=self.chosen_loopback_address,
			game_port=self.chosen_game_proxy_port,
			http_host=self.chosen_loopback_address,
			http_port=self.chosen_http_proxy_port)
		_place_files_in_directory_for_testing(
			ambassador_script_path=_get_path_relative_to_file("../../ambassador_prototyping.py"),
			ambassador_package_path=_get_path_relative_to_file("../../requiem_ambassador"),
			destination_directory_path=self._temp_directory_path,
			destination_script_name="ambassador_prototyping.py",
			destination_config_name="ambassador_prototyping.cfg",
			destination_config_string=ambassador_config_string)
		ambassador_script_path = os.path.join(self._temp_directory_path, "ambassador_prototyping.py")
		self._application_process = _start_application_and_wait_for_port_availability(
			python_path=sys.executable,
			ambassador_path=ambassador_script_path,
			game_host=self.chosen_loopback_address,
			game_port=self.chosen_game_proxy_port,
			http_host=self.chosen_loopback_address,
			http_port=self.chosen_http_proxy_port)

	# The above fixture has it setup to proxy to example.com. This is currently a manual/exploratory test,
	# we can keep running this and see if this test case class is working as a side effect.
	async def test_should_proxy_main_cdn_prefix_to_example_dot_com_as_setup_on_this_class(self):
		http_client = httpx.AsyncClient()
		# This will be removed after more exploratory testing and development of this initial test infrastructure.
		test_endpoint = f"http://{self.chosen_loopback_address}:{self.chosen_http_proxy_port}/main-cdn/index.html"
		response_body = (await http_client.get(test_endpoint)).content
		self.assertIn(b"Example Domain", response_body)