import configparser

from requiem_ambassador.http_proxy.routing import RoutingConfiguration


class AmbassadorForwardOptions:
	# to start with, the server used will be a single instance, and configured in the release
	def __init__(self,
				 upstream_game_websocket_url: str):
		self.upstream_game_websocket_url = upstream_game_websocket_url

	@classmethod
	def from_config_file(cls, path: str) -> "AmbassadorForwardOptions":
		config = configparser.ConfigParser()
		config.read(path)
		upstream_game_websocket = config.get("forwarding", "upstream_game_websocket")
		return AmbassadorForwardOptions(upstream_game_websocket)


class AmbassadorHTTPForwardOptions:
	def __init__(self,
				 main_api_base_url: str,
				 main_cdn_base_url: str,
				 image_cdn_base_url: str,
				 game_image_cdn_base_url: str,
				 cdn_dynamic_base_url: str,
				 cdn_dynamic_common_base_url: str):
		"""
		:param main_api_base_url: example: http://www.example.com/ow/
		:param main_cdn_base_url: example: http://cdn-ssl.example.com/ow/
		:param image_cdn_base_url: example: http://cdn-ssl.example.com/i/
		:param cdn_dynamic_base_url: example: http://s3e-main.example.com/shared/
		:param cdn_dynamic_common_base_url: example: http://s3e-images.example.com/shared/
		"""
		self.main_api_base_url = main_api_base_url
		self.main_cdn_base_url = main_cdn_base_url
		self.image_cdn_base_url = image_cdn_base_url
		self.game_image_cdn_base_url = game_image_cdn_base_url
		self.cdn_dynamic_base_url = cdn_dynamic_base_url
		self.cdn_dynamic_common_url = cdn_dynamic_common_base_url

	@staticmethod
	def from_config_file(file_path: str):
		parser = configparser.ConfigParser()
		parser.read(file_path)
		main_api_base_url = parser.get("forwarding-http", "main_api_base_url")
		main_cdn_base_url = parser.get("forwarding-http", "main_cdn_base_url")
		image_cdn_base_url = parser.get("forwarding-http", "image_cdn_base_url")
		cdn_dynamic_base_url = parser.get("forwarding-http", "cdn_dynamic_base_url")
		cdn_dynamic_common_url = parser.get("forwarding-http", "cdn_dynamic_common_base_url")
		return AmbassadorHTTPForwardOptions(
			main_api_base_url=main_api_base_url,
			main_cdn_base_url=main_cdn_base_url,
			image_cdn_base_url=image_cdn_base_url,
			game_image_cdn_base_url=image_cdn_base_url,
			cdn_dynamic_base_url=cdn_dynamic_base_url,
			cdn_dynamic_common_base_url=cdn_dynamic_common_url)


	def to_routing_configuration(self) -> RoutingConfiguration:
		return RoutingConfiguration(
			main_api_base_url=self.main_api_base_url,
			main_cdn_base_url=self.main_cdn_base_url,
			image_cdn_base_url=self.image_cdn_base_url,
			game_image_cdn_base_url=self.game_image_cdn_base_url,
			cdn_dynamic_base_url=self.cdn_dynamic_base_url,
			cdn_dynamic_common_base_url=self.cdn_dynamic_common_url)


class AmbassadorListenOptions:

	def __init__(self, http_host: str, http_port: int, game_host: str, game_port: int):
		self._http_port = http_port
		self._http_host = http_host
		self._game_host = game_host
		self._game_port = game_port

	@property
	def http_host(self) -> str:
		return self._http_host

	@property
	def http_port(self) -> int:
		return self._http_port

	@property
	def game_host(self) -> str:
		return self._game_host

	@property
	def game_port(self) -> int:
		return self._game_port

	@classmethod
	def from_config_file(cls, path: str) -> "AmbassadorListenOptions":
		parser = configparser.ConfigParser()
		parser.read(path)
		http_proxy_host = parser.get("listening", "http_proxy_host")
		http_proxy_port = int(parser.get("listening", "http_proxy_port"))
		game_proxy_host = parser.get("listening", "game_proxy_host")
		game_proxy_port = int(parser.get("listening", "game_proxy_port"))
		return AmbassadorListenOptions(http_proxy_host, http_proxy_port, game_proxy_host, game_proxy_port)


class AmbassadorLaunchOptions:
	"""
	The launch settings for getting the game client started. At this point the ambassador is meant
	to be shipped with a wrapper that will automatically connect to the ambassador and get told which
	SWF it should load for the game client.
	"""
	def __init__(self,
				 wrapper_captive_runtime_path: str,
				 original_game_client_swf_path: str):
		"""
		:param wrapper_captive_runtime_path: The path to use when executing a command to start the wrapper that has a captive runtime made for it.
		:param original_game_client_swf_path: The path to the swf to tell the wrapper to load for the game client.
		"""
		# if not os.path.exists(original_game_client_swf_path):
		# 	raise ValueError(f"path for captive runtime to execute {wrapper_captive_runtime_path} does not exist")
		# if not os.path.isfile(original_game_client_swf_path):
		# 	raise ValueError(f"path for captive runtime to execute {wrapper_captive_runtime_path} is not a file")
		self._wrapper_captive_runtime_path = wrapper_captive_runtime_path
		self._original_game_client_swf_location = original_game_client_swf_path

	@property
	def wrapper_captive_runtime_path(self) -> str:
		return self._wrapper_captive_runtime_path

	@property
	def original_game_game_client_swf_path(self) -> str:
		return self._original_game_client_swf_location

	@classmethod
	def from_config_file(cls, path: str) -> "AmbassadorLaunchOptions":
		parser = configparser.ConfigParser()
		parser.read(path)
		wrapper_captive_runtime_path = parser.get("launching", "wrapper_captive_runtime_path")
		original_game_client_swf_location = parser.get("launching", "original_game_client_swf_path")
		return AmbassadorLaunchOptions(wrapper_captive_runtime_path, original_game_client_swf_location)


class AmbassadorConfig:
	def __init__(self,
				 listen_options: AmbassadorListenOptions,
				 forward_options: AmbassadorForwardOptions,
				 http_forward_options: AmbassadorHTTPForwardOptions,
				 launch_options: AmbassadorLaunchOptions):
		self._listen_options = listen_options
		self._forward_options = forward_options
		self._launch_options = launch_options
		self._http_forward_options = http_forward_options

	@property
	def listen_options(self):
		return self._listen_options

	@property
	def forward_options(self):
		return self._forward_options

	@property
	def http_forward_options(self) -> AmbassadorHTTPForwardOptions:
		return self._http_forward_options
