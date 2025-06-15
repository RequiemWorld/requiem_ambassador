from __future__ import annotations
import os
import shutil
import tempfile
import subprocess


class AirSDKExecutionHelper:
	def __init__(self, adt_path: str, mxmlc_path: str):
		"""
		:param adt_path: path to a file that can be executed for using the adt (air development tool) utility.
		:param mxmlc_path: path to a file that can be executed for using the mxmlc compiler utility.
		"""
		assert os.path.exists(adt_path)
		assert os.path.exists(mxmlc_path)
		self._adt_path = adt_path
		self._mxmlc_path = mxmlc_path

	@classmethod
	def from_environment_path(cls):
		adt_path = shutil.which("adt")
		mxmlc_path = shutil.which("mxmlc")
		return AirSDKExecutionHelper(adt_path, mxmlc_path)

	def execute_adt(self, arguments: list[str], cwd: str | None = None) -> None:
		command = [self._adt_path]
		command += arguments
		subprocess.check_call(command, cwd=cwd)

	def execute_mxmlc(self, arguments: list[str], cwd: str | None = None) -> None:
		command = [self._mxmlc_path]
		command += arguments
		subprocess.check_call(command, cwd=cwd)



class ActionscriptCompilationHelper:
	"""
	- With the air sdk specifically.
	- With compression explicitly (whichever is default for the compiler version)
	- Without debug information.
	"""
	def __init__(self, sdk_execution_helper: AirSDKExecutionHelper):
		self._sdk_execution_helper = sdk_execution_helper

	def compile_actionscript_to_swf(self, root_actionscript_file: str, output_swf_path: str):
		compiler_arguments = [
			root_actionscript_file,
			"-output", output_swf_path,
			"-compress=true",
			"-debug=false"]
		self._sdk_execution_helper.execute_mxmlc(compiler_arguments)

class AIREphemeralSelfSigningHelper:
	"""
	A class for helping with the process of self signing an executable,
	by generating a certificate on the spot and filling in the necessary arguments.
	"""
	def __init__(self, execution_helper: AirSDKExecutionHelper):
		self._execution_helper = execution_helper
		self._temp_directory = tempfile.TemporaryDirectory()
		self._keystore_password = "password"
		self._pkcs12_file_path = os.path.join(self._temp_directory.name, "signing.p12")
		self._has_pkcs12_been_generated = False

	def generate_pkcs12_file(self):
		if self._has_pkcs12_been_generated:
			raise RuntimeError
		arguments = [
			"-certificate",
			"-cn", "RequiemWorld",
			"-validityPeriod", "15",  # years
			"2048-RSA",  # key
			self._pkcs12_file_path,  # output
			"password"]
		self._execution_helper.execute_adt(arguments)
		self._has_pkcs12_been_generated = True

	def get_signing_options(self) -> list[str]:
		if not self._has_pkcs12_been_generated:
			raise RuntimeError
		signing_options = [
			"-storetype", "pkcs12",
			"-keystore", self._pkcs12_file_path,
			"-storepass", self._keystore_password,
			# keeps getting errors if any server is used for this, so I've set it to None
			# since it probably doesn't even apply to self signed certificates anyway.
			"-tsa", "none"]
		return signing_options



class ApplicationDescriptorBuilder:
	def __init__(self):
		self._identifier = "com.requiemworld.airhelper"
		self._version_number = "0.0"
		self._window_title = ""
		self._window_height: int | None = None
		self._window_width: int | None = None
		self._content_swf_name: str | None = None # not sure if this is explicitly a name, or if it can be a path
		self._file_name_without_extension: str = "AirHelper"

	def with_window_title(self, title: str):
		self._window_title = title
		return self

	def with_window_height(self, height: int) -> ApplicationDescriptorBuilder:
		self._window_height = height
		return self

	def with_window_width(self, width: int) -> ApplicationDescriptorBuilder:
		self._window_width = width
		return self

	def with_identifier(self, identifier: str) -> ApplicationDescriptorBuilder:
		self._identifier = identifier
		return self

	def with_content(self, content_filename: str):
		"""
		The name of the file co-located with the descriptor file at bundle time that will be the root of the application.
		"""
		self._content_swf_name = content_filename

	def with_version_number(self, version_number: str):
		self._version_number = version_number

	def with_file_name_without_extension(self, file_name_without_extension: str) -> ApplicationDescriptorBuilder:
		self._file_name_without_extension = file_name_without_extension
		return self

	def build(self, output_path: str):
		if self._content_swf_name is None:
			raise ValueError

		# filename can end up named FileName.exe.exe
		descriptor = f"""<?xml version="1.0" encoding="utf-8" ?>
		<application xmlns="http://ns.adobe.com/air/application/51.0">
		    <id>{self._identifier}</id> 
		    <versionNumber>{self._version_number}</versionNumber> 
		    <filename>{self._file_name_without_extension}</filename> 

		    <name>Air Helper</name> 
		    <description></description> 
		    <copyright></copyright> 

		    <initialWindow> 
		        <title>{self._window_title}</title> 
		        <content>application.swf</content> 
		        <systemChrome>standard</systemChrome> 
		        <transparent>false</transparent> 
		        <visible>true</visible> 
		        <minimizable>true</minimizable> 
		        <maximizable>true</maximizable> 
		        <resizable>true</resizable> 
		    </initialWindow> 

		    <!-- 
		    More options:
		    http://livedocs.adobe.com/flex/3/html/File_formats_1.html#1043413
		    -->
		</application>"""
		with open(output_path, "w") as f:
			f.write(descriptor)


class SimplifiedBundlingOptions:
	def __init__(self,
				 output_captive_runtime_root: str,
				 executable_name_in_directory: str,
				 application_version_number: str,
				 application_window_title: str):
		"""
		:param output_captive_runtime_root: The directory that the files for the captive runtime will go directly in e.g. where RequiemWorld.exe and requiem_world.swf would go.
		:param executable_name_in_directory: The name that the executable for the captive runtime should have in the directory e.g. RequiemWorld.exe
		"""
		self._output_captive_runtime_root = output_captive_runtime_root
		self._executable_name_in_directory = executable_name_in_directory
		self._application_version_number = application_version_number
		self._application_window_title = application_window_title

	@property
	def output_captive_runtime_root(self):
		return self._output_captive_runtime_root

	@property
	def executable_name_in_directory(self):
		return self._executable_name_in_directory

	@property
	def application_version_number(self):
		return self._application_version_number

	@property
	def application_window_title(self):
		return self._application_window_title


class SwfToCaptiveRuntimeHelper:
	"""
	A class for helping with the process of taking a SWF file, producing an application
	descriptor for it, creating a throw away signing key, and producing a captive runtime for it.
	"""
	def __init__(self,
				 source_swf_path: str,
				 execution_helper: AirSDKExecutionHelper,
				 bundling_options: SimplifiedBundlingOptions):
		self._source_swf_path = source_swf_path
		self._execution_helper = execution_helper
		self._bundling_options = bundling_options

	def _run_bundle_command(self,
							captive_runtime_output_directory: str,
							application_descriptor_path: str,
							swf_name_relative_to_descriptor: str) -> None:
		captive_runtime_output_directory = os.path.abspath(captive_runtime_output_directory)
		signing_options_helper = AIREphemeralSelfSigningHelper(self._execution_helper)
		signing_options_helper.generate_pkcs12_file()
		command_arguments = ["-package"]
		command_arguments += signing_options_helper.get_signing_options()
		command_arguments += ["-target", "bundle"]
		command_arguments += [
			captive_runtime_output_directory,
			application_descriptor_path,
			swf_name_relative_to_descriptor,  # the name of the main SWF located near the descriptor
		]
		working_directory = os.path.dirname(application_descriptor_path)
		self._execution_helper.execute_adt(command_arguments, cwd=working_directory)

	def produce_captive_runtime(self):
		with tempfile.TemporaryDirectory() as temp_directory:
			swf_copy_path = os.path.join(temp_directory, "application.swf")
			descriptor_output_path = os.path.join(temp_directory, "application.xml")
			shutil.copy(self._source_swf_path, swf_copy_path)
			descriptor_builder = ApplicationDescriptorBuilder()
			descriptor_builder.with_window_title(self._bundling_options.application_window_title)
			descriptor_builder.with_version_number(self._bundling_options.application_version_number)
			descriptor_builder.with_content("application.swf")
			descriptor_builder.with_file_name_without_extension(self._bundling_options.executable_name_in_directory)
			descriptor_builder.build(descriptor_output_path)
			self._run_bundle_command(self._bundling_options.output_captive_runtime_root, descriptor_output_path, "application.swf")


class ActionscriptToCaptiveRuntimeHelper:
	def __init__(self,
				 execution_helper: AirSDKExecutionHelper,
				 bundling_options: SimplifiedBundlingOptions,
				 actionscript_file_path: str):
		self._execution_helper = execution_helper
		self._bundling_options = bundling_options
		self._actionscript_file_path = actionscript_file_path
		self._compilation_helper = ActionscriptCompilationHelper(execution_helper)

	def produce_captive_runtime(self):
		with tempfile.TemporaryDirectory() as temp_directory:
			compiled_swf_path = os.path.join(temp_directory, "application.swf")
			self._compilation_helper.compile_actionscript_to_swf(self._actionscript_file_path, compiled_swf_path)
			swf_to_captive_runtime_helper = SwfToCaptiveRuntimeHelper(
				source_swf_path=compiled_swf_path,
				execution_helper=self._execution_helper,
				bundling_options=self._bundling_options)
			swf_to_captive_runtime_helper.produce_captive_runtime()