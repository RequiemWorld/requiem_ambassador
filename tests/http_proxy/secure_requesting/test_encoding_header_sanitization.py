from . import SecureRequestingUseCaseTestFixture



# Maybe the applied strategy doesn't make total sense alone, if there is a content/transfer encoding,
# it would be because the client broadcasted that it could accept it. And maybe it should
# instead be removed from the request sent out, and the response should be outright blocked if it has any.
class TestContentEncodingHeaderSanitization(SecureRequestingUseCaseTestFixture):
	"""
	Assures that when the content is encoded with anything, and we are unable to see
	the SWF/other content that would be there, that the client isn't given the information to decode it either.
	"""

	async def test_should_return_response_without_content_encoding_when_it_is_in_original_only_in_title_casing(self):

		self._make_and_set_response_for_url("http://127.80.70.20/", headers={"Content-Encoding": "2", "Foot": "der"})
		response = await self._make_any_request_through_use_case_to_url("http://127.80.70.20/")
		self.assertEqual({"Foot": "der"}, response.headers)

	# dependent on the above test for full confidence
	async def test_should_return_response_without_content_encoding_when_it_is_in_original_in_any_casing(self):
		self._make_and_set_response_for_url("http://127.80.70.20/", headers={"ContEnT-EnCoding": "1", "Head": "der"})
		response = await self._make_any_request_through_use_case_to_url("http://127.80.70.20/")
		self.assertEqual({"Head": "der"}, response.headers)

	async def test_should_return_response_without_content_encoding_when_original_has_it_in_multiple_casings(self):
		headers = {
			"Normal": "Value",
			"Content-Encoding": "1",
			"ConTeNt-EncOdIng": "1",
		}
		self._make_and_set_response_for_url("http://127.80.70.20/", headers=headers)
		response = await self._make_any_request_through_use_case_to_url("http://127.80.70.20/")
		self.assertEqual({"Normal": "Value"}, response.headers)


class TestTransferEncodingSanitization(SecureRequestingUseCaseTestFixture):
	"""
	Content-Encoding dictates the type of encoding (compression from what I've seen) on the content,
	and the client can use it to decode it and have the original content.

	Failure for us to recognize this would mean that we wouldn't detect SWF files that show up
	as other arbitrary binary data, malicious ones would be let through, and the client would execute them.

	The above is why we remove the content-encoding header, and the same is the case for transfer-encoding,
	with the difference that it is only supposed to last in transit from one proxy to another. I believe that
	transfer-encoding could be used identically to pose the same risk as content-encoding in practice.
	"""
	async def test_should_return_response_without_transfer_encoding_when_original_only_has_it_in_title_casing(self):
		headers = {
			"Value": "one",
			"Transfer-Encoding": "abc"
		}
		self._make_and_set_response_for_url("http://127.3.2.1", headers=headers)
		response = await self._make_any_request_through_use_case_to_url("http://127.3.2.1")
		self.assertEqual({"Value": "one"}, response.headers)


	async def test_should_return_response_without_transfer_encoding_when_original_has_it_in_any_casing(self):
		headers = {
			"Ya": "hoo",
			"TrAnSfEr-EnCoDiNg": "efg"
		}
		self._make_and_set_response_for_url("http://127.7.8.9", headers=headers)
		response = await self._make_any_request_through_use_case_to_url("http://127.7.8.9")
		self.assertEqual({"Ya": "hoo"}, response.headers)

	async def test_should_return_response_without_transfer_encoding_when_original_has_it_in_multiple_casings(self):
		headers = {
			"Val": "ue",
			"Transfer-Encoding": "abc",
			"transfer-encoding": "def",
			"TrAnSfEr-EnCoDiNg": "hij",
		}
		self._make_and_set_response_for_url("http://127.60.70.80", headers=headers)
		response = await self._make_any_request_through_use_case_to_url("http://127.60.70.80")
		self.assertEqual({"Val": "ue"}, response.headers)