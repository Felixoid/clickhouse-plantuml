#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev

from typing import List, Tuple, Optional
from . import Client, Column
from token import tok_name
from tokenize import generate_tokens
from io import StringIO


class Table(object):
    """
    Represents ClickHouse table from **system.tables**

    Parameters
    ----------
    database : `str`
    name : `str`
    dependencies : `List[str]`
    create_table_query : `str`
    engine : `str`
    engine_full : `str`
    partition_key : `str`
    sorting_key : `str`
    primary_key : `str`
    sampling_key : `str`

    Attributes
    ----------
    columns : `List[Column]`
        Columns of the table
    rev_dependencies : `List[str]`
        Calculated tables this depends on
    __engine_args : `List[str]`
        Engine's arguments
    """

    def __init__(
        self,
        database: str,
        name: str,
        dependencies: List[str],
        create_table_query: str,
        engine: str,
        engine_full: str,
        partition_key: str,
        sorting_key: str,
        primary_key: str,
        sampling_key: str,
    ):
        self.database = database
        self.name = name
        self.dependencies = dependencies
        self.rev_dependencies = []  # type: List[str]
        self.create_table_query = create_table_query
        self.engine = engine
        self.engine_full = engine_full
        self.partition_key = partition_key
        self.sorting_key = sorting_key
        self.primary_key = primary_key
        self.sampling_key = sampling_key
        self.columns = []  # type: List[Column]

    def add_column(self, column: Column):
        """
        Add a column to self.columns
        """
        if not isinstance(column, Column):
            raise TypeError("column argument must be a Column")
        elif not str(self) == column.db_table:
            raise KeyError(
                "column {} argument must belong to table: {} not {}".format(
                    str(column), column.db_table, str(self)
                )
            )
        self.columns.append(column)

    def parse_engine(self, client: Optional[Client] = None):
        """
        Parses :attr:`engine_full` and gets key-value parameters for known
        tables engines. Adds new attributes.

        Attributes
        ----------
        engine_config : `List[Tuple[str, str]]`
            ordered key-velue parameters for engine
        """
        self._client = client or None
        self._parse_engine_config()
        self.engine_config = []  # type: List[Tuple[str, str]]
        self.replication_config = []  # type: List[Tuple[str, str]]
        if self.engine.startswith("Replicated"):
            self._replicated()
            engine_method = "_" + self.engine[10:].lower()
        else:
            engine_method = "_" + self.engine.lower()

        if hasattr(self, engine_method):
            getattr(self, engine_method)()
        delattr(self, "_client")

    def _replicated(self):
        """
        Creates and fills :attr:`replication_config` for Replicated* engines
        """
        self.replication_config.append(("zoo_path", self.__engine_args.pop(0)))
        self.replication_config.append(("replica", self.__engine_args.pop(0)))

    def _graphitemergetree(self):
        self._append_engine_config("rollup_config")

    def _replacingmergetree(self):
        if self.__engine_args:
            self._append_engine_config("version")

    def _summingmergetree(self):
        if self.__engine_args:
            self._append_engine_config("version")

    def _collapsingmergetree(self):
        self._append_engine_config("sign")

    def _versionedcollapsingmergetree(self):
        self._append_engine_config("sign")
        self._append_engine_config("version")

    def _odbc(self):
        self._append_engine_config("settings")
        self._append_engine_config("database")
        self._append_engine_config("table")

    def _jdbc(self):
        self._append_engine_config("uri")
        self._append_engine_config("database")
        self._append_engine_config("table")

    def _mysql(self):
        self._append_engine_config("host:port")
        self._append_engine_config("database")
        self._append_engine_config("table")
        self._append_engine_config("user")
        self._append_engine_config("password")
        if self.__engine_args:
            self._append_engine_config("replace_query")
        if self.__engine_args:
            self._append_engine_config("on_duplicate")

    def _distributed(self):
        self._append_engine_config("cluster")
        self._append_engine_config("database")
        self._append_engine_config("table")
        if self.__engine_args:
            self._append_engine_config("sharding_key")
        if self.__engine_args:
            self._append_engine_config("policy")

        self.rev_dependencies.append(
            self.engine_config[1][1] + "." + self.engine_config[2][1]
        )

    def _merge(self):
        self._append_engine_config("database")
        self._append_engine_config("table_re")
        rdeps_rows = self._client.execute(
            """
            SELECT groupArray(concat(database, '.', name)) AS rdeps
            FROM system.tables
            WHERE database = %(db)s
                AND match(name, %(re)s)
            """,
            {"db": self.engine_config[0][1], "re": self.engine_config[1][1]},
        )
        self.rev_dependencies = list(rdeps_rows["rdeps"])

    def _join(self):
        self._append_engine_config("strictness")
        self._append_engine_config("type")
        k = 1
        while self.__engine_args:
            self._append_engine_config("k{}".format(k))
            k += 1

    def _buffer(self):
        self._append_engine_config("database")
        self._append_engine_config("table")
        self._append_engine_config("num_layers")
        self._append_engine_config("min_time")
        self._append_engine_config("max_time")
        self._append_engine_config("min_rows")
        self._append_engine_config("max_rows")
        self._append_engine_config("min_bytes")
        self._append_engine_config("max_bytes")
        self.dependencies.append(
            "{}.{}".format(self.engine_config[0][1], self.engine_config[1][1])
        )

    def _append_engine_config(self, name):
        "Dangerous method, doesn't check if :attr:`__engine_args` is empty"
        self.engine_config.append((name, self.__engine_args.pop(0)))

    def _parse_engine_config(self):
        """
        Helper for parsing engine_full string and write list of parameters to
        :attr:`__engine_args`
        """
        tokens = generate_tokens(StringIO(self.engine_full).readline)
        engine_args = []  # type: List[str]
        stack = 0
        for tok in tokens:
            exact_type = tok_name[tok.exact_type]
            if exact_type == "LPAR":
                # Counting config depth
                stack += 1
                config_element = tok.string
                if stack == 1:
                    # If it's the first level - continue
                    continue
            elif exact_type == "RPAR":
                stack -= 1
                config_element = tok.string
                if stack == 0:
                    # The config is over
                    break
            elif exact_type == "COMMA" and stack == 1:
                # Collect commas from subconfigs
                # This is error prune in case of wrong config, e.g.:
                # SomeEngine('parameter1',)
                # But this is comming from ClickHouse server,
                # so we should be safe
                engine_args.append("")
                continue
            elif exact_type == "STRING":
                # Get strings from raw config strings
                config_element = eval(tok.string)
            else:
                config_element = tok.string

            if not stack:
                # continue unless we're in config parenthesis
                continue

            if not engine_args:
                engine_args.append("")

            engine_args[-1] += config_element

        self.__engine_args = engine_args

    def __str__(self):
        return "{}.{}".format(self.database, self.name)
