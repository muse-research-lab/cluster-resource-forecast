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

import apache_beam as beam
import json


def _AssignKeys(row):
    return (str(row["collection_id"]) + "-" + str(row["instance_index"]), row)


class _Unpack(beam.DoFn):
    def process(self, data):
        usage_dict = data["usage"]
        event_dict = data["event"]
        vm_sample = {}
        for d in (usage_dict, event_dict):
            vm_sample.update(d)
        return [vm_sample]


class _MergeByOrder(beam.DoFn):
    def process(self, data):
        _, streams = data
        usage_stream = streams.get("usage")
        event_stream = streams.get("event")
        if (usage_stream) and (event_stream):
            usage_stream = usage_stream[0]
            event_stream = event_stream[0]
            selected_events = []
            for event in event_stream:
                event["resource_request"] = json.loads(event["resource_request"])
                if (
                    event["resource_request"]["cpus"] > 0
                    and event["resource_request"]["memory"] > 0
                ):
                    selected_events.append(event)

            sorted_selected_events = sorted(selected_events, key=lambda x: x["time"], reverse=True)
            sorted_usage_stream = sorted(usage_stream, key=lambda x: x["start_time"], reverse=True)

            i = 0
            picked_event = sorted_selected_events[i]

            for usage in sorted_usage_stream:
                while picked_event["time"] > usage["start_time"]:
                    i = i + 1
                    if i < len(sorted_selected_events):
                        picked_event = sorted_selected_events[i]
                    else:
                        picked_event = None
                        break
                
                if picked_event != None:
                    yield dict(usage=usage, event=picked_event)
                else:
                    break
        else:
            return dict(usage=[], event=[])


def JoinUsageAndEvent(input_usage, input_event):
    keyed_usage = input_usage | "Assign Keys to Usage" >> beam.Map(_AssignKeys)
    usage_stream = keyed_usage | "Group Usage by Keys" >> beam.GroupByKey()

    keyed_event = input_event | "Assign Keys to Event" >> beam.Map(_AssignKeys)
    event_stream = keyed_event | "Group Event by Keys" >> beam.GroupByKey()

    joined_stream = (
        dict(usage=usage_stream, event=event_stream)
        | "Join Usage and Events" >> beam.CoGroupByKey()
    )
    ordered_stream = joined_stream | "Merge Usage and Events by Order" >> beam.ParDo(
        _MergeByOrder()
    )
    unpacked_stream = ordered_stream | "Unpack Usage and Event Data" >> beam.ParDo(
        _Unpack()
    )

    return unpacked_stream
