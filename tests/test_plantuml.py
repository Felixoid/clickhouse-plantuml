import unittest
from clickhouse_plantuml import plantuml


class TestPlantuml(unittest.TestCase):

    def test_plantuml_header(self):
        assert plantuml.plantuml_header() == '''@startuml
!define Table(x) class x << (T,mistyrose) >>
!define View(x) class x << (V,lightblue) >>
!define MaterializedView(x) class x << (m,orange) >>
!define Distributed(x) class x << (D,violet) >>

hide empty methods
hide stereotypes
skinparam classarrowcolor gray

'''

    def test_plantuml_footer(self):
        assert plantuml.plantuml_footer() == '@enduml'

    def test_table_macros(self):
        assert plantuml.table_macros('MaterializedView') == 'MaterializedView'
        assert plantuml.table_macros('View') == 'View'
        assert plantuml.table_macros('Distributed') == 'Distributed'
        assert plantuml.table_macros('SomeRandEngine') == 'Table'
