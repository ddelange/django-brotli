# -*- encoding: utf-8 -*-
# ! python3
import gzip
from typing import Mapping, Optional
from unittest import TestCase

import brotli
from django.middleware.gzip import GZipMiddleware

from django_brotli.middleware import BrotliMiddleware, MIN_LEN_FOR_RESPONSE_TO_PROCESS
from tests.utils import UTF8_LOREM_IPSUM


class FakeRequestAcceptsBrotli(object):
    META = {
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate, sdch, br'
    }


class FakeLegacyRequest(object):
    META = {
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate, sdch'
    }


class FakeResponse(object):
    streaming = False

    def __init__(self, content: str, headers: Optional[Mapping[str, str]] = None, streaming: Optional[bool] = None):
        self.content = content.encode(encoding='utf-8')
        self.headers = headers or {}

        if streaming:
            self.streaming = streaming

    def has_header(self, header: str) -> bool:
        return header in self.headers

    def __getitem__(self, header: str) -> str:
        return self.headers[header][0]

    def __setitem__(self, header: str, value: str):
        self.headers[header] = value


class MiddlewareTestCase(TestCase):
    def test_middleware_compress_response(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = UTF8_LOREM_IPSUM
        fake_response = FakeResponse(content=response_content)

        brotli_middleware = BrotliMiddleware()
        brotli_response = brotli_middleware.process_response(fake_request, fake_response)

        decompressed_response = brotli.decompress(data=brotli_response.content)  # type: bytes
        self.assertEqual(response_content, decompressed_response.decode(encoding='utf-8'))

    def test_middleware_wont_compress_response_if_response_is_small(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = "Hello World"

        self.assertLess(len(response_content), MIN_LEN_FOR_RESPONSE_TO_PROCESS)  # a < b

        fake_response = FakeResponse(content=response_content)

        brotli_middleware = BrotliMiddleware()
        brotli_response = brotli_middleware.process_response(fake_request, fake_response)

        self.assertEqual(response_content, brotli_response.content.decode(encoding='utf-8'))

    def test_middleware_wont_compress_if_client_not_accept(self):
        fake_request = FakeLegacyRequest()
        response_content = UTF8_LOREM_IPSUM
        fake_response = FakeResponse(content=response_content)

        brotli_middleware = BrotliMiddleware()
        brotli_response = brotli_middleware.process_response(fake_request, fake_response)

        self.assertEqual(response_content, brotli_response.content.decode(encoding='utf-8'))

    def test_middleware_wont_compress_if_response_is_already_compressed(self):
        fake_request = FakeRequestAcceptsBrotli()
        response_content = UTF8_LOREM_IPSUM
        fake_response = FakeResponse(content=response_content)

        brotli_middleware = BrotliMiddleware()
        gggbrotli_middleware = GZipMiddleware()

        gggbrotli_response = gggbrotli_middleware.process_response(fake_request, fake_response)
        brotli_response = brotli_middleware.process_response(fake_request, gggbrotli_response)

        self.assertEqual(response_content, gzip.decompress(brotli_response.content).decode(encoding='utf-8'))
