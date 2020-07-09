#!/usr/bin/env python

# License: Apache-2.0
# Copyright (C) 2020 Mikhail f. Shiryaev

"""
The scrip accepts ClickHouse credentials, databases and tables, and produces
the PlantULM schema description. Optionally it could invoke `plantuml` and
create the graphical output.
"""

import logging
import sys

from argparse import (
    ArgumentParser,
    ArgumentDefaultsHelpFormatter,
    Namespace,
    FileType,
)
from hashlib import sha1
from os.path import isfile, splitext
from pprint import pformat
from subprocess import Popen, PIPE

from . import Client, Tables
from .plantuml import plantuml_tables

logger = logging.getLogger("clickhouse-plantuml")
formatter = logging.Formatter(
    "%(levelname)-8s [%(filename)s:%(lineno)d]:\n%(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


def parse_args() -> Namespace:
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        usage="Gets the info about tables' schamas from ClickHouse database "
        "and generates PlantUML diagram source code.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="set the script verbosity, could be used multiple",
    )
    clickhouse = parser.add_argument_group("ClickHouse parameters")
    clickhouse.add_argument(
        "--host", default="localhost", help="ClickHouse server hostname",
    )
    clickhouse.add_argument(
        "--port", default=9000, type=int, help="ClickHouse server hostname",
    )
    clickhouse.add_argument(
        "-u", "--user", default="default", help="ClickHouse username",
    )
    clickhouse.add_argument(
        "-p", "--password", default="", help="ClickHouse username",
    )
    clickhouse.add_argument(
        "-d",
        "--database",
        dest="databases",
        action="append",
        default=[],
        help="databases to describe. If omitted, `default` database is used",
    )
    clickhouse.add_argument(
        "-t",
        "--table",
        action="append",
        dest="tables",
        default=[],
        help="tables whitelist to describe. If set, only mentioned tables will"
        "be queried from the server",
    )

    plantuml = parser.add_argument_group("PlantUml parameters")
    plantuml.add_argument(
        "-P",
        "--run-plantuml",
        action="store_true",
        dest="run_plantuml",
        help="if set, plantuml binary will be executed",
    )
    plantuml.add_argument(
        "-F",
        "--plantuml-format",
        choices=[
            "png",
            "svg",
            "eps",
            "pdf",
            "vdx",
            "xmi",
            "scxml",
            "html",
            "txt",
            "utxt",
            "latex",
            "latex:nopreamble",
        ],
        default="png",
        help="PlantUML output format",
    )
    plantuml.add_argument(
        "--plantuml-arguments",
        default="",
        help="additional parameters to pass into plantuml command",
    )

    diagram = parser.add_argument_group("diagram parameters")
    diagram.add_argument(
        "-o",
        "--text-output",
        type=FileType("w"),
        default="-",
        help="file to write a generated diagram source",
    )
    diagram.add_argument(
        "-O",
        "--diagram-output",
        type=FileType("w"),
        help="file to write a generated diagram. If `--text-output` is set, "
        "the default name is calculated as `filename_without_extension`."
        "`plantuml-format`. If omitted, the default name is sha1 hexdigest "
        "out of diagram content.",
    )

    args = parser.parse_args()
    args.databases = args.databases or ["default"]
    return args


def run_plantuml(args: Namespace, diagram: str):
    diagram_bin = diagram.encode("UTF-8")
    if args.run_plantuml and args.diagram_output is None:
        if args.text_output == sys.stdout:
            file_name = sha1(diagram_bin).hexdigest()
            args.diagram_output = "{}.{}".format(
                file_name, args.plantuml_format
            )
            if isfile(args.diagram_output):
                logger.info(
                    "File {} exists, do not run plantuml".format(
                        args.diagram_output
                    )
                )
                return
        else:
            args.diagram_output = "{}.{}".format(
                splitext(args.text_output.name)[0], args.plantuml_format,
            )
    logger.info("Generating file {}".format(args.diagram_output))
    command = ["plantuml", "-p", "-t" + args.plantuml_format]
    command.extend(args.plantuml_arguments.split())
    proc = Popen(command, stdout=PIPE, stdin=PIPE)
    if proc.stdin is not None:
        proc.stdin.write(diagram_bin)
    with open(args.diagram_output, "bw") as out:
        out.write(proc.communicate()[0])


def main():
    args = parse_args()
    log_levels = [logging.CRITICAL, logging.WARN, logging.INFO, logging.DEBUG]
    logger.setLevel(log_levels[min(args.verbose, 3)])
    logger.debug("Arguments are {}".format(pformat(args.__dict__)))
    client = Client(
        host=args.host, port=args.port, user=args.user, password=args.password
    )
    tables = Tables(client, args.databases, args.tables)
    logger.debug("Tables are: {}".format(pformat(list(map(str, tables)))))
    if not tables:
        logger.critical("There are no tables with given parameters")
        sys.exit(2)
    logger.debug(
        "Columns of the first table are {}".format(
            pformat([c.__dict__ for c in tables[0].columns])
        )
    )
    diagram = plantuml_tables(tables)
    args.text_output.write(diagram)
    if args.text_output != sys.stdout:
        args.text_output.close()

    if args.run_plantuml:
        run_plantuml(args, diagram)


if __name__ == "__main__":
    main()
