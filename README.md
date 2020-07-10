![Python package](https://github.com/Felixoid/clickhouse-plantuml/workflows/Python%20package/badge.svg)

# PlantUML generator for ClickHouse tables

This is a very early version of diagrams generator. It parses `system.tables` table and produces [PlantUML](https://plantuml.com) diagrams source. Here's example of produced diagram:

```plantuml
@startuml
' This diagram is generated with https://github.com/Felixoid/clickhouse-plantuml
!define Table(x) class x << (T,mistyrose) >>
!define View(x) class x << (V,lightblue) >>
!define MaterializedView(x) class x << (m,orange) >>
!define Distributed(x) class x << (D,violet) >>

hide empty methods
hide stereotypes
skinparam classarrowcolor gray

Distributed(graphite.data) {
  ENGINE=**Distributed**
  ..engine config..
  cluster: graphite_data
  database: graphite
  table: data_lr
  sharding_key: cityHash64(Path)
  ==columns==
  Path: String
  Value: Float64
  Time: UInt32
  Date: Date
  Timestamp: UInt32
}

Table(graphite.data_lr) {
  ENGINE=**ReplicatedGraphiteMergeTree**
  ..engine config..
  rollup_config: graphite_rollup
  ..replication..
  zoo_path: /clickhouse/tables/graphite.data_lr/{shard}
  replica: {replica}
  ==columns==
  Path: String <size:15><&signal></size>
  Value: Float64
  Time: UInt32 <size:15><&signal></size>
  Date: Date <size:15><&list-rich></size>
  Timestamp: UInt32
  ..<size:15><&list-rich></size>partition key..
  toYYYYMMDD(toStartOfInterval(Date, toIntervalDay(3)))
  ..<size:15><&signal></size>sorting key..
  Path, Time
}

Table(graphite.index) {
  ENGINE=**ReplicatedReplacingMergeTree**
  ..engine config..
  version: Version
  ..replication..
  zoo_path: /clickhouse/tables/graphite.index/1
  replica: {replica}
  ==columns==
  Date: Date <size:15><&list-rich></size> <size:15><&signal></size>
  Level: UInt32 <size:15><&signal></size>
  Path: String <size:15><&signal></size>
  Version: UInt32
  ..<size:15><&list-rich></size>partition key..
  toYYYYMM(Date)
  ..<size:15><&signal></size>sorting key..
  Level, Path, Date
}

Table(graphite.tagged) {
  ENGINE=**ReplicatedReplacingMergeTree**
  ..engine config..
  version: Version
  ..replication..
  zoo_path: /clickhouse/tables/graphite.tagged/1
  replica: {replica}
  ==columns==
  Date: Date <size:15><&list-rich></size> <size:15><&signal></size>
  Tag1: String <size:15><&signal></size>
  Path: String <size:15><&signal></size>
  Tags: Array(String)
  Version: UInt32
  ..<size:15><&list-rich></size>partition key..
  toYYYYMM(Date)
  ..<size:15><&signal></size>sorting key..
  Tag1, Path, Date
}

graphite.data_lr -|> graphite.data
@enduml
```

And how it looks after running PlantUML:  
![example](./docs/example.png)

## Usage

```bash
python setup.py install
clickhouse-plantuml
```
