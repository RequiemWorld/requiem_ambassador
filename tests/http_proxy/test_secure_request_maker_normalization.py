from . import SecureRequestingUseCaseTestFixture


class TestDuplicateHeaderNormalization(SecureRequestingUseCaseTestFixture):

	async def test_should_return_only_one_and_with_title_casing_when_multiple_casings_are_in_original(self):
		duplicate_headers = {
			"header-name": "abc",
			"HeAder-NaMe": "abc"}
		self._make_and_set_response_for_url(url="http://127.0.2.5", headers=duplicate_headers)
		sanitized_response = await self._make_any_request_through_use_case_to_url("http://127.0.2.5")
		self.assertEqual({"Header-Name": "abc"}, sanitized_response.headers)

