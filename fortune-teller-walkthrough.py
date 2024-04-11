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

from google.protobuf import text_format 
import argparse
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
import logging

from simulator.align_by_time import AlignByTime
from simulator.set_abstract_metrics import SetAbstractMetrics
from simulator.filter_vmsample import FilterVMSample
from simulator.reset_and_shift_simulated_time import ResetAndShiftSimulatedTime
from simulator.set_scheduler import SetScheduler
from simulator.fortune_teller import CallFortuneTellerRunner
from simulator.fortune_teller_factory import PredictorFactory
from simulator.config_pb2 import SimulationConfig
from simulator.avg_predictor import AvgPredictor
from simulator.max_predictor import MaxPredictor
from simulator.per_vm_percentile_predictor import PerVMPercentilePredictor
from simulator.per_machine_percentile_predictor import PerMachinePercentilePredictor
from simulator.n_sigma_predictor import NSigmaPredictor
from simulator.limit_predictor import LimitPredictor
from simulator.previous_predictor import PreviousPredictor
from simulator.borg_predictor import BorgPredictor
from simulator.localmax_predictor import LocalmaxPredictor
from simulator.double_max_predictor import DoubleMaxPredictor
from simulator.triple_max_predictor import TripleMaxPredictor
from simulator.transform_to_simulation_schema import TransformToSimulationSchema

from beam_mysql.connector import splitters
from beam_mysql.connector.io import ReadFromMySQL, WriteToMySQL

def main(argv=None, save_main_session=False):
    """Main entry point; defines and runs the simulator pipeline."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_file",
        dest="config_file",
        required=True,
        help="Config file based on config.proto.",
    )

    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline = beam.Pipeline(options=pipeline_options)

    f = open(known_args.config_file, "rb")
    configs = SimulationConfig()
    text_format.Parse(f.read(), configs)
    f.close()
    # TODO: Fix bad runtime order

    # Read Input Data
    input_data_query = "SELECT * FROM {}".format(
        configs.input.table
    )
    input_data = pipeline | "Query Input Table" >> ReadFromMySQL(
        host=configs.input.host,
        port=configs.input.port,
        user=configs.input.username,
        password=configs.input.password,
        database=configs.input.database,
        query=input_data_query,
        splitter=splitters.LimitOffsetSplitter(configs.input.batch_size or 1000000)
    )

    # Transform to simulation schema
    transformed_data = input_data | "Transform Data to Simulation Schema" >> beam.Map(
        TransformToSimulationSchema
    )

    # Filter VMSamples
    filtered_samples = FilterVMSample(transformed_data, configs)

    if configs.filtered_samples.HasField("input"):
        pipeline = beam.Pipeline(options=pipeline_options)
        filtered_samples_query = "SELECT * FROM {}".format(
            configs.filtered_samples.input.table
        )
        filtered_samples = pipeline | "Query Filtered Samples Table" >> ReadFromMySQL(
            host=configs.filtered_samples.input.host,
            port=configs.filtered_samples.input.port,
            user=configs.filtered_samples.input.username,
            password=configs.filtered_samples.input.password,
            database=configs.filtered_samples.input.database,
            query=filtered_samples_query,
            splitter=splitters.LimitOffsetSplitter(configs.filtered_samples.input.batch_size or 1000000)
        )

        # TODO: Filtered samples schema? Same as input. Transform filtered samples to schema. Do we need filtered samples? No, if we are able to pass an input data query or use filtering config to execute it
    
    # Time Align Samples
    time_aligned_samples = AlignByTime(filtered_samples)

    if configs.time_aligned_samples.HasField("input"):
        pipeline = beam.Pipeline(options=pipeline_options)
        time_aligned_samples_query = "SELECT * FROM {}".format(
            configs.time_aligned_samples.input.table
        )
        time_aligned_samples = (
            pipeline
            | "Query Time Aligned Samples Table"
            >> ReadFromMySQL(
                host=configs.time_aligned_samples.input.host,
                port=configs.time_aligned_samples.input.port,
                user=configs.time_aligned_samples.input.username,
                password=configs.time_aligned_samples.input.password,
                database=configs.time_aligned_samples.input.database,
                query=time_aligned_samples_query,
                splitter=splitters.LimitOffsetSplitter(configs.time_aligned_samples.input.batch_size or 1000000)
            )
        )

        # TODO: Time aligned schema of db? Transform to (sim time, sim machine, sample)?

    # Setting Abstract Metrics
    samples_with_abstract_metrics = SetAbstractMetrics(time_aligned_samples, configs)

    if configs.samples_with_abstract_metrics.HasField("input"):
        pipeline = beam.Pipeline(options=pipeline_options)
        samples_with_abstract_metrics_query = "SELECT * FROM {}".format(
            configs.samples_with_abstract_metrics.input.table
        )
        samples_with_abstract_metrics = (
            pipeline
            | "Query Samples With Abstract Metrics Table"
            >> ReadFromMySQL(
                host=configs.samples_with_abstract_metrics.input.host,
                port=configs.samples_with_abstract_metrics.input.port,
                user=configs.samples_with_abstract_metrics.input.username,
                password=configs.samples_with_abstract_metrics.input.password,
                database=configs.samples_with_abstract_metrics.input.database,
                query=samples_with_abstract_metrics_query,
                splitter=splitters.LimitOffsetSplitter(configs.samples_with_abstract_metrics.input.batch_size or 1000000)
            )
        )

        # TODO: With abstract metrics schema of db? Same with time aligned + abstract metrics not zero? Transform to (sim time, sim machine, sample)?

    # Resetting and Shifting
    if configs.reset_and_shift.reset_time_to_zero == True:
        samples_with_reset_and_shift = ResetAndShiftSimulatedTime(
            samples_with_abstract_metrics, configs
        )
    else:
        samples_with_reset_and_shift = samples_with_abstract_metrics

    if configs.samples_with_reset_and_shift.HasField("input"):
        pipeline = beam.Pipeline(options=pipeline_options)
        samples_with_reset_and_shift_query = "SELECT * FROM {}".format(
            configs.samples_with_reset_and_shift.input.table
        )
        samples_with_reset_and_shift = (
            pipeline
            | "Query Samples With Time Reset and Shift"
            >> ReadFromMySQL(
                host=configs.samples_with_reset_and_shift.input.host,
                port=configs.samples_with_reset_and_shift.input.port,
                user=configs.samples_with_reset_and_shift.input.username,
                password=configs.samples_with_reset_and_shift.input.password,
                database=configs.samples_with_reset_and_shift.input.database,
                query=samples_with_reset_and_shift_query,
                splitter=splitters.LimitOffsetSplitter(configs.samples_with_reset_and_shift.input.batch_size or 1000000)
            )
        )

        # TODO: With reset and shift schema of db? Same with with abstract metrics schema? Transform to (sim time, sim machine, sample)?

    # Setting Scheduler
    scheduled_samples = SetScheduler(samples_with_reset_and_shift, configs)

    if configs.scheduled_samples.HasField("input"):
        pipeline = beam.Pipeline(options=pipeline_options)
        scheduled_samples_query = "SELECT * FROM {}".format(
            configs.scheduled_samples.input.table
        )
        scheduled_samples = pipeline | "Query Scheduled Samples" >> ReadFromMySQL(
            host=configs.scheduled_samples.input.host,
            port=configs.scheduled_samples.input.port,
            user=configs.scheduled_samples.input.username,
            password=configs.scheduled_samples.input.password,
            database=configs.scheduled_samples.input.database,
            query=scheduled_samples_query,
            splitter=splitters.LimitOffsetSplitter(configs.scheduled_samples.input.batch_size or 1000000)
        )

        # TODO: Scheduled samples schema of db? Same with with reset and shift schema? Transform to (sim time, sim machine, sample)?

    # Calling FortuneTeller Runner
    CallFortuneTellerRunner(scheduled_samples, configs)

    # Saving Filtered Samples
    if configs.filtered_samples.HasField("output"):
        filtered_samples | "Write Filtered Samples" >> WriteToMySQL(
            host=configs.filtered_samples.output.host,
            port=configs.filtered_samples.output.port,
            user=configs.filtered_samples.output.username,
            password=configs.filtered_samples.output.password,
            database=configs.filtered_samples.output.database,
            table=configs.filtered_samples.output.table,
            batch_size=configs.filtered_samples.output.batch_size or 500
        )

    # Saving Time Aligned Samples
    if configs.time_aligned_samples.HasField("output"):
        time_aligned_samples | "Write Time Aligned Samples" >> WriteToMySQL(
            host=configs.time_aligned_samples.output.host,
            port=configs.time_aligned_samples.output.port,
            user=configs.time_aligned_samples.output.username,
            password=configs.time_aligned_samples.output.password,
            database=configs.time_aligned_samples.output.database,
            table=configs.time_aligned_samples.output.table,
            batch_size=configs.time_aligned_samples.output.batch_size or 500
        )

    # Saving Samples with Abstract Metrics
    if configs.samples_with_abstract_metrics.HasField("output"):
        samples_with_abstract_metrics | "Write Samples With Abstract Metrics" >> WriteToMySQL(
            host=configs.samples_with_abstract_metrics.output.host,
            port=configs.samples_with_abstract_metrics.output.port,
            user=configs.samples_with_abstract_metrics.output.username,
            password=configs.samples_with_abstract_metrics.output.password,
            database=configs.samples_with_abstract_metrics.output.database,
            table=configs.samples_with_abstract_metrics.output.table,
            batch_size=configs.samples_with_abstract_metrics.output.batch_size or 500
        )

    # Saving Samples with Time Reset and Shift
    if configs.samples_with_reset_and_shift.HasField("output"):
        samples_with_reset_and_shift | "Write Reset and Shifted Samples" >> WriteToMySQL(
            host=configs.samples_with_reset_and_shift.output.host,
            port=configs.samples_with_reset_and_shift.output.port,
            user=configs.samples_with_reset_and_shift.output.username,
            password=configs.samples_with_reset_and_shift.output.password,
            database=configs.samples_with_reset_and_shift.output.database,
            table=configs.samples_with_reset_and_shift.output.table,
            batch_size=configs.samples_with_reset_and_shift.output.batch_size or 500
        )

    # Saving Scheduled Samples
    if configs.scheduled_samples.HasField("output"):
        scheduled_samples | "Write Scheduled Samples" >> WriteToMySQL(
            host=configs.scheduled_samples.output.host,
            port=configs.scheduled_samples.output.port,
            user=configs.scheduled_samples.output.username,
            password=configs.scheduled_samples.output.password,
            database=configs.scheduled_samples.output.database,
            table=configs.scheduled_samples.output.table,
            batch_size=configs.scheduled_samples.output.batch_size or 500
        )

    result = pipeline.run()
    result.wait_until_finish()


if __name__ == "__main__":
    PredictorFactory().RegisterPredictor(
        "per_vm_percentile_predictor", lambda config: PerVMPercentilePredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "per_machine_percentile_predictor",
        lambda config: PerMachinePercentilePredictor(config),
    )
    PredictorFactory().RegisterPredictor(
        "n_sigma_predictor", lambda config: NSigmaPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "max_predictor", lambda config: MaxPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "limit_predictor", lambda config: LimitPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "avg_predictor", lambda config: AvgPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "previous_predictor", lambda config: PreviousPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "borg_predictor", lambda config: BorgPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "localmax_predictor", lambda config: LocalmaxPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "double_max_predictor", lambda config: DoubleMaxPredictor(config)
    )
    PredictorFactory().RegisterPredictor(
        "triple_max_predictor", lambda config: TripleMaxPredictor(config)
    )
    logging.getLogger().setLevel(logging.INFO)
    main()
