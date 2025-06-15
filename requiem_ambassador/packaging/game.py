

def create_dummy_config_file(file_path: str) -> None:
	"""
	Creates a dummy version of the config file required in
	the data directory for the game client to load.
	"""
	dummy_config_data = """
	<config>
	<param name="prod" value="http://www.example.com/ow"/>
	<param name="currentServer" value="default"/>
	<param name="lastMessageId" value="0"/>
    <param name="supportedAppStore" value="disable"/>
	<param name="store_url" value="https://example.com/ow/exampleDownload.jsp"/>
	<param name="config_version" value="0"/>
	</config>
	"""
	with open(file_path, "w") as f:
		f.write(dummy_config_data)
