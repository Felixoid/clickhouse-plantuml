#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterator


class Client:
    """
    Minimal ClickHouse HTTP client using stdlib only.
    Authenticates via X-ClickHouse-User / X-ClickHouse-Key headers to avoid
    encoding issues with special characters in credentials.
    """

    def __init__(self, url: str, user: str = "default", password: str = None):
        self._url = url.rstrip("/")
        self._headers = {"X-ClickHouse-User": user}
        if password is not None:
            self._headers["X-ClickHouse-Key"] = password

    def execute_iter_dict(
        self, query: str, params: Dict[str, Any] = None
    ) -> Iterator[Dict[str, Any]]:
        """Execute a query and yield each row as a dict."""
        if params:
            query = self._bind(query, params)
        full_query = query.strip() + " FORMAT JSONEachRow"
        url = f"{self._url}/?" + urllib.parse.urlencode({"query": full_query})
        req = urllib.request.Request(url, headers=self._headers)
        try:
            with urllib.request.urlopen(req) as resp:
                for line in resp:
                    line = line.strip()
                    if line:
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError as e:
                            raise RuntimeError(
                                f"Unexpected response from ClickHouse: {line!r}\n"
                                f"URL: {url}"
                            ) from e
        except urllib.error.HTTPError as e:
            raise RuntimeError(e.read().decode()) from e

    def execute(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a query and return the first row as a dict."""
        return next(iter(self.execute_iter_dict(query, params)), {})

    @staticmethod
    def _escape(value: str) -> str:
        """Escape single quotes for SQL string literals."""
        return value.replace("'", "''")

    def _bind(self, query: str, params: Dict[str, Any]) -> str:
        """
        Inline parameter binding for %(name)s placeholders.
        Tuples become ('a', 'b') IN-clause literals.
        Scalar strings are single-quoted.
        """
        bound = {}
        for key, val in params.items():
            if isinstance(val, tuple):
                bound[key] = "(" + ", ".join(f"'{self._escape(v)}'" for v in val) + ")"
            else:
                bound[key] = f"'{self._escape(val)}'"
        return query % bound
