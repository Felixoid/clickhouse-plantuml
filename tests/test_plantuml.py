import unittest
from clickhouse_plantuml import plantuml


class TestPlantuml(unittest.TestCase):
    def test_plantuml_header(self):
        assert plantuml.plantuml_header() == (
            "@startuml\n"
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

    def test_plantuml_footer(self):
        assert plantuml.plantuml_footer() == "@enduml"

    def test_table_macros(self):
        assert plantuml.table_macros("MaterializedView") == "MaterializedView"
        assert plantuml.table_macros("View") == "View"
        assert plantuml.table_macros("Distributed") == "Distributed"
        assert plantuml.table_macros("SomeRandEngine") == "Table"
