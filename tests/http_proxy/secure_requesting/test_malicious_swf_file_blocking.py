from . import SecureRequestingUseCaseTestFixture


class TestBlockingOfFlashFilesystemFile(SecureRequestingUseCaseTestFixture):

	async def test_should_no_compression_variants_of_swf_files_which_use_flash_filesystem_file(self):
		await self._verifyUseCaseWillBlockResponseWithSwfSampleFile("FlashFilesystemFile-fws.swf")

	async def test_should_zlib_compression_variants_of_swf_files_which_use_flash_filesystem_file(self):
		await self._verifyUseCaseWillBlockResponseWithSwfSampleFile("FlashFilesystemFile-cws.swf")


	async def test_should_lzma_compression_variants_of_swf_files_which_use_flash_filesystem_file(self):
		await self._verifyUseCaseWillBlockResponseWithSwfSampleFile("FlashFilesystemFile-zws.swf")



