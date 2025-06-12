# copied from 2023 Ambassador code. All the code in this
# file is now an implementation detail of the secure request making UseCase.
from __future__ import annotations
import io
import zlib
import lzma
from typing import BinaryIO

ZLIB_SWF_HEADER = b"CWS"
LZMA_SWF_HEADER = b"ZWS"
NORMAL_SWF_HEADER = b"FWS"

SWF_HEADERS = [
	ZLIB_SWF_HEADER,
	LZMA_SWF_HEADER,
	NORMAL_SWF_HEADER
]


BLACKLISTED_LIBRARY_STRINGS = [
	"flash.net",
	"flash.filesystem",
	"flash.external",
	"flash.html",
	"flash.desktop",
	"flash.system",
	# outright block anything that mentions 'loader' i.e. URLLoader, flash.display.Loader
	"loader",
	"getDefinitionByName",
]


def has_swf_header(data: bytes) -> bool:
	"""
	Check if the data starts with one of the three SWF headers.
	:return: Returns true if it starts with one of three SWF headers.
	"""
	return any(data.startswith(header) for header in SWF_HEADERS)

# SWF scanning code copied from the original ambassador from 2023

def read_swf_data(buffer: BinaryIO) -> bytes:
	"""
	Read SWF data (starting at the signature) from a buffer
	and return the compressed part non-compressed if compressed.
	"""
	header = buffer.read(3)  # signature (3)
	buffer.seek(5, io.SEEK_CUR)  # version (1) + size (4) (5)
	if header == ZLIB_SWF_HEADER:
		return zlib.decompress(buffer.read())
	elif header == LZMA_SWF_HEADER:
		# https://stackoverflow.com/questions/32787778/python-2-7-pylzma-works-python-3-4-lzma-module-does-not
		buffer.seek(4, io.SEEK_CUR)  # uncompressed size (4)
		return lzma.decompress(buffer.read(5) + b"\xff" * 8 + buffer.read())
	elif header == NORMAL_SWF_HEADER:
		# TODO assure that this will actually return the main part of the SWF
		return buffer.read()
	else:
		raise Exception("bad SWF header")


def scan_swf_data(swf_data: bytes, libraries: list[str], max_findings=None) -> list[str]:
	"""
	Returns a list of library strings that are found in the swf data
	after converting both to lowercase and checking for them.

	Checks for libraries until max_findings are found or when there's no
	libraries left in the checklist to check for.
	"""
	check_data = swf_data.lower()
	check_list = [lib.lower().encode() for lib in libraries]
	found_libraries = []
	for library in check_list:
		if library in check_data:
			found_libraries.append(library.decode())
		if max_findings is not None and len(found_libraries) == max_findings:
			break

	return found_libraries


def scan_swf_data_blacklisted_libraries(swf_data: bytes) -> list[str]:

	"""
	Checks if the non-compressed SWF data contains strings for any of
	the blacklisted libraries in it's bytecode. Returns a list of blacklisted
	libraries that were found in the SWF.
	"""
	return scan_swf_data(swf_data, BLACKLISTED_LIBRARY_STRINGS)
