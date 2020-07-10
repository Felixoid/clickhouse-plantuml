import unittest
from unittest.mock import patch
from clickhouse_plantuml import plantuml as p


class DummyColumn(p.Column):
    def __init__(self):
        pass


class TestPlantuml(unittest.TestCase):
    def setUp(self):
        self.test_table_data = {
            "database": "test_database",
            "name": "test_table",
            "dependencies": ["database.table"],
            "create_table_query": "SOME LONG STRING",
            "engine": "ReplicatedReplacingMergeTree",
            "engine_full": (
                "ReplicatedReplacingMergeTree('/zk/node', 'replica_name', "
                "'ver') PARTITION BY date ORDER BY date"
            ),
            "partition_key": "date",
            "sorting_key": "date",
            "primary_key": "date",
            "sampling_key": "",
        }
        self.test_table = p.Table(**self.test_table_data)
        self.test_table.parse_engine()
        self.test_tables = p.Tables(None)
        self.test_tables.append(self.test_table)

    def tearDown(self):
        del self.test_table
        del self.test_tables

    def test_plantuml(self):
        assert (
            p.plantuml_tables([]) == p.plantuml_header() + p.plantuml_footer()
        )

    def test_plantuml_header(self):
        assert p.plantuml_header() == (
            "@startuml\n"
            "' This diagram is generated with "
            "https://github.com/Felixoid/clickhouse-plantuml\n"
            "!define Table(x) class x << (T,mistyrose) >>\n"
            "!define View(x) class x << (V,lightblue) >>\n"
            "!define MaterializedView(x) class x << (m,orange) >>\n"
            "!define Distributed(x) class x << (D,violet) >>\n"
            "\n"
            "hide empty methods\n"
            "hide stereotypes\n"
            "skinparam classarrowcolor gray\n"
            "\n"
        )

    @patch.object(
        p, "gen_tables_dependencies", return_value="mocked_dependencies"
    )
    @patch.object(p, "gen_table", return_value="mocked_table")
    def test_gen_tables(self, mock_table, mock_dependencies):
        # The substatements will be testet separately
        assert p.gen_tables([]) == "mocked_dependencies"
        assert p.gen_tables(self.test_tables) == (
            "mocked_table" "mocked_dependencies"
        )
        mock_table.assert_called_once_with(self.test_table)
        mock_dependencies.assert_called_with(self.test_tables)

    def test_plantuml_footer(self):
        assert p.plantuml_footer() == "@enduml\n"

    @patch.object(p, "gen_table_columns", return_value="mocked_columns\n")
    @patch.object(p, "gen_table_engine", return_value="mocked_engine\n")
    def test_gen_table(self, mock_engine, mock_columns):
        assert p.gen_table(self.test_table) == (
            "Table(test_database.test_table) {\n"
            "  mocked_engine\n"
            "  mocked_columns\n"
            "}\n\n"
        )
        mock_engine.assert_called_once_with(self.test_table)
        mock_columns.assert_called_once_with(self.test_table)

    def test_gen_tables_dependencies(self):
        another_table = dict(self.test_table_data)
        another_table.update(
            {
                "database": "database",
                "name": "table",
                "dependencies": ["test_database.test_table"],
            }
        )
        tables = self.test_tables
        tables.append(p.Table(**another_table))
        tables[0].rev_dependencies = ["test_database.test_table"]
        tables[1].rev_dependencies = ["database.table"]
        assert p.gen_tables_dependencies(tables) == (
            "test_database.test_table -|> database.table\n"
            "test_database.test_table -|> test_database.test_table\n"
            "database.table -|> test_database.test_table\n"
            "database.table -|> database.table\n"
        )

    def test_table_macros(self):
        assert p.table_macros("MaterializedView") == "MaterializedView"
        assert p.table_macros("View") == "View"
        assert p.table_macros("Distributed") == "Distributed"
        assert p.table_macros("SomeRandEngine") == "Table"

    def test_gen_table_engine(self):
        assert p.gen_table_engine(self.test_table) == (
            "ENGINE=**ReplicatedReplacingMergeTree**\n"
            "..engine config..\n"
            "version: ver\n"
            "..replication..\n"
            "zoo_path: /zk/node\n"
            "replica: replica_name\n"
        )

    @patch.object(p, "column_keys", return_value="")
    def test_gen_table_column(self, mock_column_keys):
        col_date = DummyColumn()
        col_date.__dict__.update(
            {
                "name": "date",
                "type": "Date",
                "database": "test_database",
                "table": "test_table",
            }
        )
        col_str = DummyColumn()
        col_str.__dict__.update(
            {
                "name": "str",
                "type": "String",
                "database": "test_database",
                "table": "test_table",
            }
        )
        self.test_table.add_column(col_date)
        self.test_table.add_column(col_str)
        self.test_table.sorting_key = "date, str"
        assert p.gen_table_columns(self.test_table) == (
            "==columns==\n"
            "date: Date\n"
            "str: String\n"
            "..<size:15><&list-rich></size>partition key..\n"
            "date\n"
            "..<size:15><&signal></size>sorting key..\n"
            "date, str\n"
            "..<size:15><&key></size>primary key..\n"
            "date\n"
        )

    def test_key_sign(self):
        assert p.column_key_sign("any random thing") == ""
        sign = "<size:15><&{}></size>"
        assert p.column_key_sign("partition") == sign.format("list-rich")
        assert p.column_key_sign("primary") == sign.format("key")
        assert p.column_key_sign("sampling") == sign.format("collapse-down")
        assert p.column_key_sign("sorting") == sign.format("signal")

    def test_column_keys(self):
        col = DummyColumn()
        keys = ["partition", "sorting", "primary", "sampling", "noize"]
        for key in keys:
            setattr(col, "is_in_{}_key".format(key), True)

        assert p.column_keys(col, keys) == (
            " <size:15><&list-rich></size>"
            " <size:15><&signal></size>"
            " <size:15><&key></size>"
            " <size:15><&collapse-down></size>"
            " "
        )
