# MySQL Database Setup

The simulator is based on data processing pipelines. This means we need a robust
way to load and store data. We pick MySQL as the input and output of the pipelines
because it a widely supported and open source variant of SQL. It allows us to handle
data easily by running SQL queries.

## Input Data

The simulator uses the Google's publicly-available [cluster usage trace](https://github.com/google/cluster-data)
and we provide tools and instructions to collect and store the required data (instance
events and instance usage) in a MySQL database. Find out more in our
[Google Trace Dataset repository](https://gitlab.software.imdea.org/muse-lab/google-trace-dataset/-/tree/main/tools)

## Output Data

The data processing pipelines of the simulator produce data belonging in one of
the following schemas (under `schemas/` folder):

- `joined_tables.json`: Output data of `simulator-setup-walkthrough.py` script.
  It is the result of a left join except that we match on nearest timestamps rather
  than equal ones. We match every *instance usage* record with the previous nearest
  in time *instance event* (if it exists) that refers to the same `collection_id`
  and `instance_index`.
- `result_without_samples.json`: Output data of `fortune-teller-walkthrough.py` script.
  It is the output of the simulator that contains time series of predicted peaks,
  total usages and limits.
- `vmsample.json`: The same schema as `joined_tables.json`. Corresponds to the output
  of filtered VM samples (see `FilterVMSample` function) which is an intermediate
  output of the simulation.
- `simulated_vmsample.json`: Similar to the schema in `vmsample.json`. It contains
  two extra fields, `simulated_time` and `simulated_machine`. Corresponds to the
  output of the following functions: `AlignByTime`, `SetAbstractMetrics`, `ResetAndShiftSimulatedTime`
  and `SetScheduler` which is an intermediate output of the simulation.

In order to store the produced data in our MySQL database we need to first create
SQL tables that correspond to the above schemas. For the scripts to work successfully,
we create tables with the following schemas:

`join_tables.json`

```sql
CREATE TABLE IF NOT EXISTS join_usage_and_event (
   `time` bigint,
   `unique_id` varchar(100),
   `collection_id` bigint,
   `instance_index` bigint,
   `priority` bigint,
   `scheduling_class` bigint,
   `machine_id` bigint,
   `alloc_collection_id` bigint,
   `alloc_instance_index` bigint,
   `collection_type` bigint,
   `avg_cpu_usage` double precision,
   `avg_memory_usage` double precision,
   `max_cpu_usage` double precision,
   `max_memory_usage` double precision,
   `random_sample_cpu_usage` double precision,
   `assigned_memory` double precision,
   `sample_rate` double precision,
   `p0_cpu_usage` double precision,
   `p10_cpu_usage` double precision,
   `p20_cpu_usage` double precision,
   `p30_cpu_usage` double precision,
   `p40_cpu_usage` double precision,
   `p50_cpu_usage` double precision,
   `p60_cpu_usage` double precision,
   `p70_cpu_usage` double precision,
   `p80_cpu_usage` double precision,
   `p90_cpu_usage` double precision,
   `p91_cpu_usage` double precision,
   `p92_cpu_usage` double precision,
   `p93_cpu_usage` double precision,
   `p94_cpu_usage` double precision,
   `p95_cpu_usage` double precision,
   `p96_cpu_usage` double precision,
   `p97_cpu_usage` double precision,
   `p98_cpu_usage` double precision,
   `p99_cpu_usage` double precision,
   `memory_limit` double precision,
   `cpu_limit` double precision,
   `abstract_usage` double precision,
   `abstract_limit` double precision
);
```

`result_without_samples.json`

```sql
CREATE TABLE IF NOT EXISTS simulation_results (
   `fortune_teller_name` varchar(100),
   `simulated_time` bigint,
   `simulated_machine` varchar(100),
   `predicted_peak` double precision,
   `total_usage` double precision,
   `limit` double precision
);
```

`vmsample.json`

```sql
CREATE TABLE IF NOT EXISTS filtered_samples (
   `time` bigint,
   `unique_id` varchar(100),
   `collection_id` bigint,
   `instance_index` bigint,
   `priority` bigint,
   `scheduling_class` bigint,
   `machine_id` bigint,
   `alloc_collection_id` bigint,
   `alloc_instance_index` bigint,
   `collection_type` bigint,
   `avg_cpu_usage` double precision,
   `avg_memory_usage` double precision,
   `max_cpu_usage` double precision,
   `max_memory_usage` double precision,
   `random_sample_cpu_usage` double precision,
   `assigned_memory` double precision,
   `sample_rate` double precision,
   `p0_cpu_usage` double precision,
   `p10_cpu_usage` double precision,
   `p20_cpu_usage` double precision,
   `p30_cpu_usage` double precision,
   `p40_cpu_usage` double precision,
   `p50_cpu_usage` double precision,
   `p60_cpu_usage` double precision,
   `p70_cpu_usage` double precision,
   `p80_cpu_usage` double precision,
   `p90_cpu_usage` double precision,
   `p91_cpu_usage` double precision,
   `p92_cpu_usage` double precision,
   `p93_cpu_usage` double precision,
   `p94_cpu_usage` double precision,
   `p95_cpu_usage` double precision,
   `p96_cpu_usage` double precision,
   `p97_cpu_usage` double precision,
   `p98_cpu_usage` double precision,
   `p99_cpu_usage` double precision,
   `memory_limit` double precision,
   `cpu_limit` double precision,
   `abstract_usage` double precision,
   `abstract_limit` double precision
);
```

`simulated_vmsample.json`

```sql
CREATE TABLE IF NOT EXISTS time_aligned_samples (
   `simulated_time` bigint,
   `simulated_machine` varchar(100),
   `time` bigint,
   `unique_id` varchar(100),
   `collection_id` bigint,
   `instance_index` bigint,
   `priority` bigint,
   `scheduling_class` bigint,
   `machine_id` bigint,
   `alloc_collection_id` bigint,
   `alloc_instance_index` bigint,
   `collection_type` bigint,
   `avg_cpu_usage` double precision,
   `avg_memory_usage` double precision,
   `max_cpu_usage` double precision,
   `max_memory_usage` double precision,
   `random_sample_cpu_usage` double precision,
   `assigned_memory` double precision,
   `sample_rate` double precision,
   `p0_cpu_usage` double precision,
   `p10_cpu_usage` double precision,
   `p20_cpu_usage` double precision,
   `p30_cpu_usage` double precision,
   `p40_cpu_usage` double precision,
   `p50_cpu_usage` double precision,
   `p60_cpu_usage` double precision,
   `p70_cpu_usage` double precision,
   `p80_cpu_usage` double precision,
   `p90_cpu_usage` double precision,
   `p91_cpu_usage` double precision,
   `p92_cpu_usage` double precision,
   `p93_cpu_usage` double precision,
   `p94_cpu_usage` double precision,
   `p95_cpu_usage` double precision,
   `p96_cpu_usage` double precision,
   `p97_cpu_usage` double precision,
   `p98_cpu_usage` double precision,
   `p99_cpu_usage` double precision,
   `memory_limit` double precision,
   `cpu_limit` double precision,
   `abstract_usage` double precision,
   `abstract_limit` double precision
);
```

Feel free to change tha name of these tables, but not the schema!
