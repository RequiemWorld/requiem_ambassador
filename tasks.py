import os.path
import zipfile
import shutil
import invoke
import tempfile
import subprocess
from requiem_ambassador.packaging.air import AirSDKExecutionHelper
from requiem_ambassador.packaging.air import SimplifiedBundlingOptions
from requiem_ambassador.packaging.air import SwfToCaptiveRuntimeHelper
from requiem_ambassador.packaging.game import create_dummy_config_file
from requiem_ambassador.packaging.zipping import zip_up_directory


def _script_to_pyinstaller_exe(input_script_path: str, output_exe_path: str):
	assert shutil.which("pyinstaller")
	pyinstaller_path = shutil.which("pyinstaller")
	absolute_script_path = os.path.abspath(input_script_path)
	# the above might not guarantee that the pyinstaller we're about to use is the
	# one for the python version that we want, we should look into it more later.
	assert input_script_path.endswith(".py"), "for simplicity sake the input script should end with .py"
	input_script_name = os.path.basename(input_script_path)[0:-3]  # removing the .py extension
	with tempfile.TemporaryDirectory() as temp_directory_path:
		command = [pyinstaller_path, absolute_script_path, "-F"]
		subprocess.check_output(command, cwd=temp_directory_path)
		expected_exe_path = os.path.join(temp_directory_path, "dist/", input_script_name + ".exe")
		shutil.copy(expected_exe_path, output_exe_path)



@invoke.task
def bundle_ambassador_and_client_windows(
		context: invoke.Context,
		game_swf_path: str,
		output_directory_path: str):
	"""
	:param game_swf_path: The path to the SWF for the game client that should have a new captive runtime built for it.
	:param output_directory_path: The path that the ambassador_prototyping.exe and built captive_runtime directory should be placed in.
	"""
	if not shutil.which("mxmlc"):
		print("mxmlc utility not found, air bin directory probably not in paths, aborting.")
		raise RuntimeError()

	with tempfile.TemporaryDirectory() as temp_directory_path:
		_script_to_pyinstaller_exe("ambassador_prototyping.py", os.path.join(temp_directory_path, "ambassador_prototyping.exe"))
		shutil.copy("ambassador_prototyping.cfg", os.path.join(temp_directory_path, "ambassador_prototyping.cfg"))
		# building a captive runtime for the game SWF and putting it alongside the ambassador.
		execution_helper = AirSDKExecutionHelper.from_environment_path()
		captive_runtime_output_path = os.path.join(temp_directory_path, "requiem-restore")
		bundling_options = SimplifiedBundlingOptions(
			output_captive_runtime_root=captive_runtime_output_path,
			executable_name_in_directory="RequiemRestore",
			application_version_number="0.0.0",
			application_window_title="Requiem Restore")
		swf_to_captive_runtime_helper = SwfToCaptiveRuntimeHelper(game_swf_path, execution_helper, bundling_options)
		swf_to_captive_runtime_helper.produce_captive_runtime()
		# the game client SWF is all we want to care about for releasing it, but alongside of it, with
		# the captive air runtime, is a necessary data directory with a config file it won't work without.
		data_directory_path = os.path.join(captive_runtime_output_path, "data")
		os.mkdir(data_directory_path)
		create_dummy_config_file(os.path.join(data_directory_path, "config.xml"))
		shutil.copytree(temp_directory_path, output_directory_path.rstrip("/\\"))

	assert os.path.exists(os.path.join(output_directory_path, "ambassador_prototyping.cfg"))
	assert os.path.exists(os.path.join(output_directory_path, "ambassador_prototyping.exe"))
	assert os.path.exists(os.path.join(output_directory_path, "requiem-restore/data/config.xml"))


@invoke.task
def bundle_ambassador_and_client_windows_zip(context: invoke.Context, game_swf_path: str, output_zip_file_path: str):
	output_zip_file_path = os.path.abspath(output_zip_file_path)
	with tempfile.TemporaryDirectory() as temp_directory_path:
		# in the root of this temporary directory should be a directory called requiem_ambassador,
		# we zip up this temp directory, and then in the archive at the root will be the normal output directory.
		ambassador_bundling_output_directory = os.path.join(temp_directory_path, "requiem_ambassador")
		bundle_ambassador_and_client_windows(context, game_swf_path, ambassador_bundling_output_directory)
		zip_up_directory(temp_directory_path, output_zip_file_path)
