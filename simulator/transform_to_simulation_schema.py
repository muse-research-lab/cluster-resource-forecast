
def TransformToSimulationSchema(vm_sample):
    if vm_sample is not None:
        vm_info = {
            "unique_id": vm_sample.get("unique_id"),
            "collection_id": vm_sample.get("collection_id"),
            "instance_index": vm_sample.get("instance_index"),
            "priority": vm_sample.get("priority", -1),
            "scheduling_class": vm_sample.get("scheduling_class", -1),
            "machine_id": vm_sample.get("machine_id"),
            "alloc_collection_id": vm_sample.get("alloc_collection_id", -1),
            "alloc_instance_index": vm_sample.get("alloc_instance_index", -100),
            "collection_type": vm_sample.get("collection_type", -1),
        }

        vm_metrics = {
            "avg_cpu_usage": vm_sample.get("avg_cpu_usage", -1),
            "avg_memory_usage": vm_sample.get("avg_memory_usage", -1),
            "max_cpu_usage": vm_sample.get("max_cpu_usage", -1),
            "max_memory_usage": vm_sample.get("max_memory_usage", -1),
            "random_sample_cpu_usage": vm_sample.get("random_sample_cpu_usage", -1),
            "assigned_memory": vm_sample.get("assigned_memory", -1),
            "sample_rate": vm_sample.get("sample_rate", -1),
            "p0_cpu_usage": vm_sample.get("p0_cpu_usage", -1),
            "p10_cpu_usage": vm_sample.get("p10_cpu_usage", -1),
            "p20_cpu_usage": vm_sample.get("p20_cpu_usage", -1),
            "p30_cpu_usage": vm_sample.get("p30_cpu_usage", -1),
            "p40_cpu_usage": vm_sample.get("p40_cpu_usage", -1),
            "p50_cpu_usage": vm_sample.get("p50_cpu_usage", -1),
            "p60_cpu_usage": vm_sample.get("p60_cpu_usage", -1),
            "p70_cpu_usage": vm_sample.get("p70_cpu_usage", -1),
            "p80_cpu_usage": vm_sample.get("p80_cpu_usage", -1),
            "p90_cpu_usage": vm_sample.get("p90_cpu_usage", -1),
            "p91_cpu_usage": vm_sample.get("p91_cpu_usage", -1),
            "p92_cpu_usage": vm_sample.get("p92_cpu_usage", -1),
            "p93_cpu_usage": vm_sample.get("p93_cpu_usage", -1),
            "p94_cpu_usage": vm_sample.get("p94_cpu_usage", -1),
            "p95_cpu_usage": vm_sample.get("p95_cpu_usage", -1),
            "p96_cpu_usage": vm_sample.get("p96_cpu_usage", -1),
            "p97_cpu_usage": vm_sample.get("p97_cpu_usage", -1),
            "p98_cpu_usage": vm_sample.get("p98_cpu_usage", -1),
            "p99_cpu_usage": vm_sample.get("p99_cpu_usage", -1),
            "memory_limit": vm_sample.get("memory_limit", -1),
            "cpu_limit": vm_sample.get("cpu_limit", -1),
        }

        abstract_metrics = {
            "usage": vm_sample.get("abstract_usage", 0),
            "limit": vm_sample.get("abstract_limit", 0)
        }

        updated_vm_sample = {
            "time": vm_sample.get("time"),
            "info": vm_info,
            "metrics": vm_metrics,
            "abstract_metrics": abstract_metrics,
        }

    else:
        updated_vm_sample = vm_sample

    return updated_vm_sample
