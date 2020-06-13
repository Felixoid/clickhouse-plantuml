import unittest
from clickhouse_plantuml import plantuml as p


class TestPlantuml(unittest.TestCase):
    def setUp(self):
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
        self.test_table = p.Table(**self.test_table_data)
        self.test_tables = p.Tables(None)
        self.test_tables.append(self.test_table)

    def test_plantuml(self):
        assert p.plantuml([]) == p.plantuml_header() + p.plantuml_footer()

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

    def test_gen_tables(self):
        # The substatements will be testet separately
        assert p.gen_tables([]) == ""

    def test_plantuml_footer(self):
        assert p.plantuml_footer() == "@enduml\n"

    def test_table_macros(self):
        assert p.table_macros("MaterializedView") == "MaterializedView"
        assert p.table_macros("View") == "View"
        assert p.table_macros("Distributed") == "Distributed"
        assert p.table_macros("SomeRandEngine") == "Table"

    def test_key_sign(self):
        assert p.key_sign("any random thing") == ""
        sign = "<size:15><&{}></size>"
        assert p.key_sign("partition") == sign.format("list-rich")
        assert p.key_sign("primary") == sign.format("key")
        assert p.key_sign("sampling") == sign.format("collapse-down")
        assert p.key_sign("sorting") == sign.format("signal")
