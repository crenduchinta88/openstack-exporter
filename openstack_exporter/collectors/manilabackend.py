import logging
import json
from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily
from manilaclient import client as manila  # Ensure the manilaclient is installed
from openstack_exporter import BaseCollector

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('openstack_exporter.exporter')

class ManilaBackendCollector(BaseCollector.BaseCollector):
    version = "1.0.0"

    def __init__(self, openstack_config, collector_config):
        super().__init__(openstack_config, collector_config)
        self.manila_client = self._manila_client()

    def _manila_client(self):
        """Create a Manila client using manilaclient."""
        os_auth_url = self.config['auth_url']
        os_username = self.config['username']
        os_password = self.config['password']
        os_project_name = self.config['project_name']
        api_version = 3.0  # Adjust the API version as needed

        client_args = {
            'region_name': self.region,
            'service_type': "share",  # Manila service type
            'endpoint_type': "publicURL",
            'insecure': False,
            'session': self.client.session,
        }

        return manila.Client(
            api_version,
            os_username,
            os_password,
            os_project_name,
            os_auth_url,
            **client_args,
        )

    def describe(self):
        # Define metrics for description
        yield GaugeMetricFamily('manila_total_capacity_gb', 'Total capacity of the Manila backend in GiB')
        yield GaugeMetricFamily('manila_free_capacity_gb', 'Free capacity of the Manila backend in GiB')
        yield GaugeMetricFamily('manila_allocated_capacity_gb', 'Allocated capacity of the Manila backend in GiB')
        yield GaugeMetricFamily('manila_reserved_percentage', 'Reserved percentage of the Manila backend')
        yield GaugeMetricFamily('manila_reserved_snapshot_percentage', 'Reserved snapshot percentage of the Manila backend')
        yield GaugeMetricFamily('manila_reserved_share_extend_percentage', 'Reserved share extend percentage of the Manila backend')
        yield GaugeMetricFamily('manila_max_over_subscription_ratio', 'Max over-subscription ratio of the Manila backend')

        yield InfoMetricFamily('manila_hardware_state_info', 'Hardware state of the Manila backend')
        yield InfoMetricFamily('manila_share_backend_name_info', 'Share backend name of the Manila backend')
        yield InfoMetricFamily('manila_driver_version_info', 'Driver version of the Manila backend')

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
        endpoint_url = "/v2/scheduler-stats/pools/detail"
        try:
            response = self.manila_client.session.get(endpoint_url)
            if response.status_code == 200:
                pools_data = json.loads(response.content.decode('utf-8'))
                pools = pools_data.get('pools', [])

                for pool in pools:
                    data = self._parse_pool_data(pool)
                    labels = [data['name'], data['pool_name'], data['share_backend_name'],
                              data['driver_version'], data['hardware_state']]

                    yield self._create_gauge_metric('manila_total_capacity_gb', 'Total capacity of the pool in GiB', data['total_capacity_gb'], labels)
                    yield self._create_gauge_metric('manila_free_capacity_gb', 'Free capacity of the pool in GiB', data['free_capacity_gb'], labels)
                    yield self._create_gauge_metric('manila_allocated_capacity_gb', 'Allocated capacity of the pool in GiB', data['allocated_capacity_gb'], labels)
                    yield self._create_gauge_metric('manila_reserved_percentage', 'Percentage of capacity reserved in the pool', data['reserved_percentage'], labels)
                    yield self._create_gauge_metric('manila_reserved_snapshot_percentage', 'Percentage of capacity reserved for snapshots in the pool', data['reserved_snapshot_percentage'], labels)
                    yield self._create_gauge_metric('manila_reserved_share_extend_percentage', 'Percentage of capacity reserved for share extension in the pool', data['reserved_share_extend_percentage'], labels)
                    yield self._create_gauge_metric('manila_max_over_subscription_ratio', 'Maximum over-subscription ratio of the pool', data['max_over_subscription_ratio'], labels)
            else:
                logger.error(f"Failed to retrieve data from Manila API. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error while collecting Manila backend metrics: {e}")

# Ensure the manilaclient package is installed in your environment
