#!/usr/bin/env python
# pylint: disable=protected-access

import unittest

from clickhouse_plantuml.client import Client


class TestClientBind(unittest.TestCase):
    def setUp(self):
        self.client = Client("http://localhost:8123")

    def test_no_password_omits_header(self):
        client = Client("http://localhost:8123")
        assert (
            "X-ClickHouse-Key" not in client._headers
        )  # pylint: disable=protected-access
        client = Client("http://localhost:8123", password=None)
        assert (
            "X-ClickHouse-Key" not in client._headers
        )  # pylint: disable=protected-access

    def test_password_sends_header(self):
        client = Client("http://localhost:8123", password="")
        assert (
            client._headers.get("X-ClickHouse-Key") == ""
        )  # pylint: disable=protected-access

        client = Client("http://localhost:8123", password="secret")
        assert (
            client._headers["X-ClickHouse-Key"] == "secret"
        )  # pylint: disable=protected-access

    def test_bind_scalar(self):
        result = self.client._bind(  # pylint: disable=protected-access
            "WHERE db = %(db)s", {"db": "mydb"}
        )
        assert result == "WHERE db = 'mydb'"

    def test_bind_tuple(self):
        result = self.client._bind(  # pylint: disable=protected-access
            "WHERE db IN %(ds)s", {"ds": ("db1", "db2")}
        )
        assert result == "WHERE db IN ('db1', 'db2')"

    def test_bind_scalar_with_quote(self):
        result = self.client._bind(  # pylint: disable=protected-access
            "WHERE db = %(db)s", {"db": "string'with'quote"}
        )
        assert result == "WHERE db = 'string''with''quote'"

    def test_bind_tuple_with_quote(self):
        result = self.client._bind(  # pylint: disable=protected-access
            "WHERE db IN %(ds)s", {"ds": ("normal", "it's")}
        )
        assert result == "WHERE db IN ('normal', 'it''s')"

    def test_escape_no_quotes(self):
        assert Client._escape("plain") == "plain"  # pylint: disable=protected-access

    def test_escape_single_quote(self):
        assert Client._escape("it's") == "it''s"  # pylint: disable=protected-access

    def test_escape_multiple_quotes(self):
        assert Client._escape("a'b'c") == "a''b''c"  # pylint: disable=protected-access
