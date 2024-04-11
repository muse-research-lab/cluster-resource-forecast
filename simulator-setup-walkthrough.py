# Copyright 2020 Google LLC.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from past.builtins import unicode

import argparse
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from beam_mysql.connector import splitters
from beam_mysql.connector.io import ReadFromMySQL, WriteToMySQL

from simulator.pair_instance_event_to_usage import JoinUsageAndEvent
from simulator.map_to_schema import MapVMSampleToSchema


def run(argv=None, save_main_session=False):
    """Main entry point; defines and runs the simulator data preparation pipeline."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", "-i",
        dest="input",
        required=True,
        help="Input file containing SQL queries for usage and events tables.",
    )
    parser.add_argument(
        "--output", "-o",
        dest="output",
        required=True,
        help=(
            "Output SQL table for results."
        ),
    )
    parser.add_argument(
        "--host",
        dest="host",
        required=True,
        help=(
            "Host name or IP of the database server."
        ),
    )
    parser.add_argument(
        "--port", "-p",
        dest="port",
        required=True,
        help=(
            "Port of the database server."
        ),
    )
    parser.add_argument(
        "--database", "-db",
        dest="database",
        required=True,
        help=(
            "Name of the database."
        ),
    )
    parser.add_argument(
        "--user", "-u",
        dest="username",
        required=True,
        help=(
            "User of the database."
        ),
    )
    parser.add_argument(
        "--pass", "-pwd",
        dest="password",
        required=True,
        help=(
            "Password of the database user."
        ),
    )

    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session
    p = beam.Pipeline(options=pipeline_options)

    queries_file = open("{}".format(known_args.input), "r")
    queries = queries_file.readlines()
    usage_query = queries[0]
    event_query = queries[1]

    input_usage = p | "Query Usage Table" >> ReadFromMySQL(
        host=known_args.host,
        port=known_args.port,
        user=known_args.username,
        password=known_args.password,
        database=known_args.database,
        query=usage_query,
        splitter=splitters.LimitOffsetSplitter()
    )
    input_event = p | "Query Event Table" >> ReadFromMySQL(
        host=known_args.host,
        port=known_args.port,
        user=known_args.username,
        password=known_args.password,
        database=known_args.database,
        query=event_query,
        splitter=splitters.LimitOffsetSplitter()
    )

    usage_event_stream = JoinUsageAndEvent(input_usage, input_event)
    final_table = usage_event_stream | "Map Joined Data to Schema" >> beam.Map(
        MapVMSampleToSchema
    )

    final_table | "Write Data to Database" >> WriteToMySQL(
        host=known_args.host,
        port=known_args.port,
        user=known_args.username,
        password=known_args.password,
        database=known_args.database,
        table=known_args.output,
        batch_size=500
    )

    result = p.run()
    result.wait_until_finish()


if __name__ == "__main__":
    run()
