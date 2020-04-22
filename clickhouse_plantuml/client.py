#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev

from clickhouse_driver import Client as OriginalClient  # type: ignore


class Client(OriginalClient):
    """
    Wrapper for clickhouse_driver.Client with execute_dict method
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute_dict(self, *args, **kwargs):
        kwargs['with_column_types'] = True
        rows, columns = self.execute(*args, **kwargs)
        result = [{columns[i][0]: v for i, v in enumerate(r)} for r in rows]
        return result

    def execute_iter_dict(self, *args, **kwargs):
        kwargs['with_column_types'] = True
        result, columns = self.execute(*args, **kwargs)
        for r in result:
            yield {columns[i][0]: v for i, v in enumerate(r)}
