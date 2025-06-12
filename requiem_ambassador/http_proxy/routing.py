from __future__ import annotations
import re
from urllib.parse import urljoin


class RoutingConfiguration:
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
		self._main_api_base_url = main_api_base_url
		self._main_cdn_base_url = main_cdn_base_url
		self._image_cdn_base_url = image_cdn_base_url
		self._game_image_cdn_base_url = game_image_cdn_base_url
		self._cdn_dynamic_base_url = cdn_dynamic_base_url
		self._cdn_dynamic_common_base_url = cdn_dynamic_common_base_url

	# these are hardcoded to match the ones meant for the main.xml config
	@property
	def main_api_path(self):
		return "/main-api/"

	@property
	def main_cdn_path(self):
		return "/main-cdn/"
	@property
	def image_cdn_path(self):
		return "/image-cdn/"

	@property
	def game_image_cdn_path(self):
		return "/game-image-cdn/"

	@property
	def cdn_dynamic_path(self):
		return "/cdn-dynamic/"

	@property
	def cdn_dynamic_common_path(self):
		return "/cdn-dynamic-common/"

	def make_main_xml_data(self, ambassador_http_host: str, ambassador_http_port: int) -> bytes:
		ambassador_base_url = f"http://{ambassador_http_host}:{ambassador_http_port}"
		data = f"""
		<supershell v="1">
			<mobile>
				<param name="url" value="http://cdn-ssl.example.com/ow/games/info/supershellair-mobile.swf"/>
				<param name="version" value="357.9243.14-a-main-2021-10-17-03"/>
				<param name="core-version" value="357.9243.14-a-core-2021-10-17-03"/>
				<param name="dsop" value="Y2wzdjNyIGhheG9yCg=="/>
				<param name="main" value="{ambassador_base_url}/main-api/"/>
				<param name="cdn" value="{ambassador_base_url}/main-cdn/"/>
				<param name="image" value="http://{ambassador_base_url}/image-cdn/"/>
				<param name="game-image" value="http://{ambassador_base_url}/game-image-cdn/"/>
				<param name="cdn-dynamic-personal" value="http://{ambassador_base_url}/"/>
				<param name="cdn-dynamic-photos" value="http://{ambassador_base_url}/cdn-dynamic/"/>
				<param name="cdn-dynamic-contests" value="http://{ambassador_base_url}/cdn-dynamic/"/>
				<param name="cdn-dynamic-crews" value="http://{ambassador_base_url}/cdn-dynamic/"/>
				<param name="cdn-dynamic-common" value="http://{ambassador_base_url}/cdn-dynamic-common/"/>
				<param name="env" value="supershell"/>
				<param name="landing" value="103"/>
				<param name="future" value="false"/>
			</mobile>

		</supershell>
		""".encode()
		return data
	def get_upstream_url_for_path(self, path: str) -> str | None:
		# prepares the path by replacing everywhere there are multiple slashes with a single slash
		normalized_path = re.sub("/+", "/", path)
		if normalized_path.startswith(self.main_api_path):
			return urljoin(self._main_api_base_url, normalized_path.replace(self.main_api_path, ""))
		elif normalized_path.startswith(self.main_cdn_path):
			return urljoin(self._main_cdn_base_url, normalized_path.replace(self.main_cdn_path, ""))
		elif normalized_path.startswith(self.image_cdn_path):
			return urljoin(self._image_cdn_base_url, normalized_path.replace(self.image_cdn_path, ""))
		elif normalized_path.startswith(self.game_image_cdn_path):
			return urljoin(self._game_image_cdn_base_url, normalized_path.replace(self.game_image_cdn_path, ""))
		elif normalized_path.startswith(self.cdn_dynamic_path):
			return urljoin(self._cdn_dynamic_base_url, normalized_path.replace(self.cdn_dynamic_path, ""))
		elif normalized_path.startswith(self.cdn_dynamic_common_path):
			return urljoin(self._cdn_dynamic_common_base_url, normalized_path.replace(self.cdn_dynamic_common_path, ""))

		return None