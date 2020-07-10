#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev

from . import Column, Table, Tables
from typing import List


def plantuml_tables(tables: Tables):
    return plantuml_header() + gen_tables(tables) + plantuml_footer()


def plantuml_header():
    # Credits
    # https://www.red-gate.com/simple-talk/sql/sql-tools/automatically-creating-uml-database-diagrams-for-sql-server/
    header = "\n".join(
        (
            "@startuml",
            "' This diagram is generated with "
            "https://github.com/Felixoid/clickhouse-plantuml",
            "!define Table(x) class x << (T,mistyrose) >>",
            "!define View(x) class x << (V,lightblue) >>",
            "!define MaterializedView(x) class x << (m,orange) >>",
            "!define Distributed(x) class x << (D,violet) >>",
            "",
            "hide empty methods",
            "hide stereotypes",
            "skinparam classarrowcolor gray",
            "",
            "",
        )
    )
    return header


def gen_tables(tables: Tables):
    """
    Generates the PlantUML source code out of the Tables object
    """
    code = ""
    for t in tables:
        code += gen_table(t)

    code += gen_tables_dependencies(tables)
    return code


def plantuml_footer():
    return "@enduml\n"


def gen_table(table: Table) -> str:
    t = table
    # Table header
    code = "{}({}) {{\n".format(table_macros(t.engine), str(t))

    code += addSpaces(gen_table_engine(t))
    code += addSpaces(gen_table_columns(t))

    # Table footer
    code += "}\n\n"
    return code


def gen_tables_dependencies(tables: Tables) -> str:
    code = ""
    for t in tables:
        code += "".join(
            "{} -|> {}\n".format(str(t), d)
            for d in t.dependencies
            if d in tables.as_dict
        )

        code += "".join(
            "{} -|> {}\n".format(r, str(t))
            for r in t.rev_dependencies
            if r in tables.as_dict
        )
    return code


def table_macros(table_type: str):
    if table_type in ("MaterializedView", "View", "Distributed"):
        return table_type
    return "Table"


def gen_table_engine(table: Table) -> str:
    t = table
    code = "ENGINE=**{}**\n".format(t.engine)
    if t.engine_config:
        code += "..engine config..\n"
    for k, v in t.engine_config:
        code += "{}: {}\n".format(k, v)

    if t.replication_config:
        code += "..replication..\n"
    for k, v in t.replication_config:
        code += "{}: {}\n".format(k, v)

    return code


def gen_table_columns(table: Table) -> str:
    t = table
    table_keys = ["partition", "sorting", "sampling"]
    if t.sorting_key != t.primary_key:
        # If primary != sorting, it's worth to append it
        table_keys.insert(2, "primary")

    code = "==columns==\n"
    for c in t.columns:
        code += "{}: {}{}\n".format(c.name, c.type, column_keys(c, table_keys))

    for k in table_keys:
        key_string = getattr(t, "{}_key".format(k))
        if key_string:
            code += "..{}{} key..\n{}\n".format(
                column_key_sign(k), k, key_string
            )

    return code


def column_key_sign(key: str) -> str:
    sign = "<size:15><&{}></size>"
    if key == "partition":
        return sign.format("list-rich")
    if key == "sorting":
        return sign.format("signal")
    if key == "primary":
        return sign.format("key")
    if key == "sampling":
        return sign.format("collapse-down")
    return ""


def column_keys(column: Column, table_keys: List[str]) -> str:
    code = ""

    for key in table_keys:
        if getattr(column, "is_in_{}_key".format(key)):
            code += " {}".format(column_key_sign(key))
    return code


def addSpaces(lines: str, amount: int = 2) -> str:
    indent = " " * amount
    return indent + indent.join(lines.splitlines(True))
