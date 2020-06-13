#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev

import logging
from typing import List, Dict
from collections.abc import MutableSequence
from . import Client, Column, Table

logger = logging.getLogger("clickhouse-plantuml")


class Tables(MutableSequence):
    """
    List of table objects
    """

    def __init__(
        self,
        client: Client,
        databases: List[str] = None,
        tables: List[str] = None,
    ):
        self.client = client
        self.__list = list()  # type: List[Table]
        self.as_dict = dict()  # type: Dict[str, Table]
        if databases:
            self._get_tables(databases, tables)
            self._get_columns()
            self._merge_matviews()

    def __delitem__(self, i):
        if isinstance(i, int):
            key = str(self.__list[i])
            del self.__list[i]
            _ = self.as_dict.pop(key)
        elif isinstance(i, str):
            table = self.as_dict.pop(i)
            self.__list.remove(table)
        elif isinstance(i, Table):
            self.__list.remove(i)
            _ = self.as_dict.pop(str(i))
        else:
            raise ValueError("Use index, table name or Table object")

    def __setitem__(self, i, t):
        if not isinstance(t, Table):
            raise ValueError("Must be an instance of Table")
        current = self.__list[i]
        self.__list[i] = t
        del self.as_dict[str(current)]
        self.as_dict[str(t)] = t

    def __getitem__(self, i):
        logger.debug("Check for i {} in self".format(i))
        if isinstance(i, int):
            return self.__list[i]
        elif isinstance(i, str):
            return self.as_dict[i]

    def __len__(self):
        return len(self.__list)

    def insert(self, i, t):
        if not isinstance(t, Table):
            raise ValueError("Must be an instance of Table")
        self.__list.insert(i, t)
        self.as_dict[str(t)] = t

    def _get_tables(self, databases: List[str], tables: List[str] = None):
        query = """
            SELECT
                database,
                name,
                arrayMap((x, y) -> concat(x, '.', y), dependencies_database,
                         dependencies_table) AS dependencies,
                create_table_query,
                engine,
                engine_full,
                partition_key,
                sorting_key,
                primary_key,
                sampling_key
            FROM system.tables
            WHERE database IN %(ds)s
                {name_clause}
            ORDER BY database, name
            """
        if tables:
            query = query.format(name_clause="AND name IN %(ns)s")
            # Here's a trick to get both normal and
            tables += [".inner." + t for t in tables]
            data = self.client.execute_dict(
                query, {"ds": tuple(databases), "ns": tuple(tables)}
            )
        else:
            query = query.format(name_clause="")
            data = self.client.execute_dict(query, {"ds": tuple(databases)},)

        self.extend(Table(**r) for r in data)
        for t in self:
            t.parse_engine(self.client)

    def _get_columns(self):
        """
        Get columns for every table in the instance
        """
        if not self:
            return
        tables = {t.name for t in self}
        databases = {t.database for t in self}
        columns_data = self.client.execute_dict(
            """
            SELECT
                database,
                table,
                name,
                type,
                default_kind,
                default_expression,
                comment,
                is_in_partition_key,
                is_in_sorting_key,
                is_in_primary_key,
                is_in_sampling_key,
                compression_codec
            FROM system.columns
            WHERE database IN %(ds)s
                AND table IN %(ts)s
            """,
            {"ds": tuple(databases), "ts": tuple(tables)},
        )
        for c in columns_data:
            column = Column(**c)
            self[column.db_table].add_column(column)

    def _merge_matviews(self):
        """
        MATERIALIZED VIEW is presented in a database as two tables:
            - `database`.`mat_view_name` - the view
            - `database`.`.inner.mat_view_name` - table with data

        This method applies inner table `*_key` and `columns` attributes to the
        MaterializedVeiw one and deletes inner from self
        """
        inners = tuple(t for t in self if t.name.startswith(".inner."))
        if not inners:
            return

        for i in inners:
            logger.debug("{} config: {}".format(i.name, i.engine_config))
            mv_name = i.name[7:]  # Strip .inner.
            mv = self["{}.{}".format(i.database, mv_name)]
            # Rename table name for each mat_view's column
            for c in i.columns:
                c.table = mv_name

            mv.engine_config = [("sub_engine", i.engine)] + i.engine_config
            for attr in (
                "partition_key",
                "sorting_key",
                "primary_key",
                "sampling_key",
                "columns",
                "replication_config",
            ):
                setattr(mv, attr, getattr(i, attr))

            self.remove(i)
