#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev

from dataclasses import dataclass, field
from typing import List

from .column import Column
from .table import Table
from .tables import Tables


@dataclass
class DiagramConfig:
    type_length: int = field(default=80)
    comment_length: int = field(default=80)


def truncate_type(s: str, max_length: int) -> str:
    """Truncate a type string, preserving the last 3 chars as a closing hint."""
    if len(s) <= max_length:
        return s
    return s[: max_length - 4] + "\u2026" + s[-3:]


def truncate_comment(s: str, max_length: int) -> str:
    """Truncate a comment string."""
    if len(s) <= max_length:
        return s
    return s[: max_length - 1] + "\u2026"


def plantuml_tables(tables: Tables, config: DiagramConfig = None):
    config = config or DiagramConfig()
    return plantuml_header() + gen_tables(tables, config) + plantuml_footer()


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


def gen_tables(tables: Tables, config: DiagramConfig):
    """
    Generates the PlantUML source code out of the Tables object
    """
    code = ""
    for t in tables:
        code += gen_table(t, config)

    code += gen_tables_dependencies(tables)
    return code


def plantuml_footer():
    return "@enduml\n"


def gen_table(table: Table, config: DiagramConfig) -> str:
    t = table
    # Table header
    code = f"{table_macros(t.engine)}({t}) {{\n"

    if t.comment:
        code += add_spaces(f"{truncate_comment(t.comment, config.comment_length)}\n")
        code += add_spaces("==\n")

    code += add_spaces(gen_table_engine(t))
    code += add_spaces(gen_table_columns(t, config))

    # Table footer
    code += "}\n\n"
    return code


def gen_tables_dependencies(tables: Tables) -> str:
    code = ""
    for t in tables:
        code += "".join(f"{t} -|> {d}\n" for d in t.dependencies if d in tables.as_dict)

        code += "".join(
            f"{r} -|> {t}\n" for r in t.rev_dependencies if r in tables.as_dict
        )
    return code


def table_macros(table_type: str):
    if table_type in ("MaterializedView", "View", "Distributed"):
        return table_type
    return "Table"


def gen_table_engine(table: Table) -> str:
    t = table
    code = f"ENGINE=**{t.engine}**\n"
    if t.engine_config:
        code += "..engine config..\n"
    for k, v in t.engine_config:
        code += f"{k}: {v}\n"

    if t.replication_config:
        code += "..replication..\n"
    for k, v in t.replication_config:
        code += f"{k}: {v}\n"

    return code


def gen_table_columns(table: Table, config: DiagramConfig) -> str:
    t = table
    table_keys = ["partition", "sorting", "sampling"]
    if t.sorting_key != t.primary_key:
        # If primary != sorting, it's worth to append it
        table_keys.insert(2, "primary")

    code = "==columns==\n"
    for c in t.columns:
        col_type = truncate_type(c.type, config.type_length)
        code += f"{c.name}: {col_type}{column_keys(c, table_keys)}\n"

    for k in table_keys:
        key_string = getattr(t, f"{k}_key")
        if key_string:
            code += f"..{column_key_sign(k)}{k} key..\n{key_string}\n"

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
        if getattr(column, f"is_in_{key}_key"):
            code += f" {column_key_sign(key)}"
    return code


def add_spaces(lines: str, amount: int = 2) -> str:
    indent = " " * amount
    return indent + indent.join(lines.splitlines(True))
