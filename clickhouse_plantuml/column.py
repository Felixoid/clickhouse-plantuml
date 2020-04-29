#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev


class Column(object):
    """
    Represents ClickHouse column
    """

    def __init__(
        self,
        database: str,
        table: str,
        name: str,
        type: str,
        default_kind: str,
        default_expression: str,
        comment: str,
        compression_codec: str,
        is_in_partition_key: bool,
        is_in_sorting_key: bool,
        is_in_primary_key: bool,
        is_in_sampling_key: bool,
    ):
        self.database = database
        self.table = table
        self.name = name
        self.type = type
        self.default_kind = default_kind
        self.default_expression = default_expression
        self.comment = comment
        self.compression_codec = compression_codec
        self.is_in_partition_key = is_in_partition_key
        self.is_in_sorting_key = is_in_sorting_key
        self.is_in_primary_key = is_in_primary_key
        self.is_in_sampling_key = is_in_sampling_key

    @property
    def db_table(self):
        return "{}.{}".format(self.database, self.table)

    def __str__(self):
        return self.name
