import unittest
from unittest.mock import Mock, patch
from clickhouse_plantuml import table


class TestTable(unittest.TestCase):
    def setUp(self):
        self.mock = Mock()
        self.test_table_data = {
            "database": "test_database",
            "name": "test_table",
            "dependencies": ["database.table"],
            "create_table_query": "SOME LONG STRING",
            "engine": "MergeTree",
            "engine_full": "MergeTree() PARTITION BY date ORDER BY date",
            "partition_key": "date",
            "sorting_key": "date",
            "primary_key": "date",
            "sampling_key": "",
        }
        self.test_table = table.Table(**self.test_table_data)

    def tearDown(self):
        del self.mock
        del self.test_table

    def test_init(self):
        for k, v in self.test_table_data.items():
            assert v == getattr(self.test_table, k)

        assert self.test_table.rev_dependencies == []
        assert self.test_table.columns == []

    def test_add_column(self):
        c = table.Column(
            "test_database",
            "test_table",
            "date",
            "Date",
            "",
            "",
            "",
            "",
            True,
            True,
            True,
            False,
        )
        self.test_table.add_column(c)
        assert self.test_table.columns == [c]
        c.table = "another_table"
        with self.assertRaises(KeyError):
            self.test_table.add_column(c)
        with self.assertRaises(TypeError):
            self.test_table.add_column("column")

    def test_parse_engine_invoke_config(self):
        t = self.test_table
        with patch.object(table.Table, "_parse_engine_config") as mock:
            t.parse_engine()
            mock.assert_called_once_with()

    def test_parse_engine_config(self):
        t = self.test_table
        t.engine_full = "SomeEngine('parameter1', 2, '', func(column))"
        t._parse_engine_config()
        assert t._Table__engine_args == ["parameter1", "2", "", "func(column)"]
        # Don't catch wrong config error
        t.engine_full = "SomeEngine('parameter1',)"
        t._parse_engine_config()
        assert t._Table__engine_args == ["parameter1", ""]

    def test_append_engine_config(self):
        t = self.test_table
        t.engine_config = []
        t._Table__engine_args = ["parameter"]
        t._append_engine_config("name")
        assert t.engine_config == [("name", "parameter")]

        # Dangerous and doesn't check if something is in __engine_args
        with self.assertRaises(IndexError):
            t._append_engine_config("name")
