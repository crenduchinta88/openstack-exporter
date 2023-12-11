import logging
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily

from openstack_exporter import BaseCollector

LOG = logging.getLogger('openstack_exporter.exporter')

class ManilaBackendCollector(BaseCollector):
    version = "1.0.0"

    def __init__(self, openstack_config, collector_config):
        super().__init__(openstack_config, collector_config)
        self.manila_client = self._manila_client()

    def _manila_client(self):
        # Use self.client to interact with Manila
        return self.client.share

    def _parse_pool_data(self, pool):
        # Parse pool data to extract metrics
        return {
            "name": pool.get('name', 'N/A'),
            "pool_name": pool.get('pool_name', 'N/A'),
            "total_capacity_gb": pool.get('total_capacity_gb', 0),
            "free_capacity_gb": pool.get('free_capacity_gb', 0),
            "allocated_capacity_gb": pool.get('allocated_capacity_gb', 0),
            "reserved_percentage": pool.get('reserved_percentage', 0),
            "reserved_snapshot_percentage": pool.get('reserved_snapshot_percentage', 0),
            "reserved_share_extend_percentage": pool.get('reserved_share_extend_percentage', 0),
            "max_over_subscription_ratio": pool.get('max_over_subscription_ratio', 1),
            "hardware_state": pool.get('hardware_state', 'N/A'),
            "share_backend_name": pool.get('share_backend_name', 'N/A'),
            "driver_version": pool.get('driver_version', 'N/A')
        }

    def _create_gauge_metric(self, name, description, value, labels):
        return GaugeMetricFamily(name, description, labels=labels, value=value)

    def collect(self):
        pools = self.manila_client.pools(detail=True)

        for pool in pools:
            data = self._parse_pool_data(pool)
            labels = [data['name'], data['pool_name'], data['share_backend_name'],
                      data['driver_version'], data['hardware_state']]

            yield self._create_gauge_metric(
                'manila_total_capacity_gb',
                'Total capacity of the pool in GiB',
                data['total_capacity_gb'],
                labels
            )

            yield self._create_gauge_metric(
                'manila_free_capacity_gb',
                'Free capacity of the pool in GiB',
                data['free_capacity_gb'],
                labels
            )

            yield self._create_gauge_metric(
                'manila_allocated_capacity_gb',
                'Allocated capacity of the pool in GiB',
                data['allocated_capacity_gb'],
                labels
            )

            yield self._create_gauge_metric(
                'manila_reserved_percentage',
                'Percentage of capacity reserved in the pool',
                data['reserved_percentage'],
                labels
            )

            yield self._create_gauge_metric(
                'manila_reserved_snapshot_percentage',
                'Percentage of capacity reserved for snapshots in the pool',
                data['reserved_snapshot_percentage'],
                labels
            )

            yield self._create_gauge_metric(
                'manila_reserved_share_extend_percentage',
                'Percentage of capacity reserved for share extension in the pool',
                data['reserved_share_extend_percentage'],
                labels
            )

            yield self._create_gauge_metric(
                'manila_max_over_subscription_ratio',
                'Maximum over-subscription ratio of the pool',
                data['max_over_subscription_ratio'],
                labels
            )
