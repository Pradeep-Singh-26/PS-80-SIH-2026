"""District & station aggregation module.

Aggregates gridded corrected forecasts, probability products, and regime
classifications to district polygons and station points.
"""


def run():
    """Run district + station aggregation pipeline stage."""
    from src.district_agg.district_aggregator import aggregate_districts
    from src.district_agg.station_aggregator import aggregate_stations

    print("  Running district aggregation ...")
    aggregate_districts()
    print("  Running station aggregation ...")
    aggregate_stations()
