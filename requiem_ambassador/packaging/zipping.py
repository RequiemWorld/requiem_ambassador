from __future__ import annotations
import os
import shutil


def zip_up_directory(directory_path: str, output_zip_file_path: str) -> None:
	assert output_zip_file_path.endswith(".zip")
	base_name_with_extension = os.path.basename(output_zip_file_path)
	base_name_without_extension = base_name_with_extension[0:-4]
	shutil.make_archive(base_name_without_extension, format="zip", root_dir=directory_path)
	shutil.move(base_name_with_extension, output_zip_file_path)
