![Python package](https://github.com/Felixoid/clickhouse-plantuml/workflows/Python%20package/badge.svg)

# PlantUML generator for ClickHouse tables

This is a very early version of diagrams generator. It parses `system.tables` table and produces [PlantUML](https://plantuml.com) diagrams source. Here's example of produced diagram:

![example](./example.png)

## Usage

```bash
python setup.py install
clickhouse-plantuml
```
