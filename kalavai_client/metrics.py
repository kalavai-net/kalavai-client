import time
import os
from datetime import datetime, timedelta

import clickhouse_connect
import pandas as pd


"""
Class used to fetch data from ClickHouse, for downstream application metrics
RJHQWQ4T
"""
class MetricsAPI():
    def __init__(self, endpoint, port, username, password):
        try:
            self.client = clickhouse_connect.get_client(
                host=endpoint,
                port=port,
                username=username,
                password=password,
                secure=True,
                # --- THE CLOUD WAKE-UP PROTECTION ---
                connect_timeout=60,       # Wait up to 60s for the initial TCP/HTTP connection
                send_receive_timeout=60,  # Wait up to 60s for the first query to return 
                query_retries=5           # Retry 5 times if the network drops/refuses during spin-up
            )
        except:
            pass
    
    def __del__(self):
        self.client.close()

    def ping_service(self, max_attempts=6, backoff_time=10):
        for attempt in range(max_attempts):
            if self.client.ping():
                print("🟢 Service is awake and ready!")
                return True
            print(f"⏳ Still waking up... (Attempt {attempt + 1}/{max_attempts})")
            time.sleep(backoff_time)
        return False

    def _query(self, query):
        df = self.client.query_df(query)
        return df.to_dict(orient="dict")

    def _create_selector(self, property, aggregate):
        if aggregate:
            return f"SUM({property}) as {property}"
        else:
            return property

    def get_compute_usage(
        self,
        user_ids: list[str],
        job_ids: list[str] = None,
        start_time: str = None,
        end_time: str = None,
        aggregate: bool = False
    ):
        """
        Get compute usage metrics for a specific user
        
        Args:
            user_id (str): The user ID to query
            start_time (str, optional): Start date for the query. Defaults to None.
            end_time (str, optional): End date for the query. Defaults to None.
            
        Returns:
            list: List of dictionaries containing usage metrics
        """
        # import json
        # if not aggregate:
        #     import pandas as pd
        #     from datetime import datetime

        #     data = [
        #         {
        #             'job_id': 'test-job',
        #             'gpu_type': 'A100',
        #             'vram_hours': 40,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5,
        #             "hour": pd.Timestamp(datetime(2026, 5, 26, 0, 0, 0)).isoformat()
        #         },
        #         {
        #             'job_id': 'test-job',
        #             'gpu_type': 'A100',
        #             'vram_hours': 10,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5,
        #             "hour": pd.Timestamp(datetime(2026, 5, 26, 1, 0, 0)).isoformat()
        #         },
        #         {
        #             'job_id': 'test-job',
        #             'gpu_type': 'A100',
        #             'vram_hours': 10,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5,
        #             "hour": pd.Timestamp(datetime(2026, 5, 26, 2, 0, 0)).isoformat()
        #         },
        #         {
        #             'job_id': 'test-job-2',
        #             'gpu_type': 'A100',
        #             'vram_hours': 5,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5,
        #             "hour": pd.Timestamp(datetime(2026, 5, 26, 0, 0, 0)).isoformat()
        #         },
        #         {
        #             'job_id': 'test-job-2',
        #             'gpu_type': 'A100',
        #             'vram_hours': 20,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5,
        #             "hour": pd.Timestamp(datetime(2026, 5, 26, 1, 0, 0)).isoformat()
        #         },
        #         {
        #             'job_id': 'test-job-2',
        #             'gpu_type': 'A100',
        #             'vram_hours': 5,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5,
        #             "hour": pd.Timestamp(datetime(2026, 5, 26, 2, 0, 0)).isoformat()
        #         }
        #     ]
        # else:
        #     data =  [
        #         {
        #             'job_id': 'test-job',
        #             'gpu_type': 'A100',
        #             'vram_hours': 120,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5
        #         },
        #         {
        #             'job_id': 'test-job-2',
        #             'gpu_type': 'A100',
        #             'vram_hours': 60,
        #             'cpu_hours': 347.1666666666667,
        #             'memory_hours': 121453.5
        #         }
        #     ]

        
        # data = [d for d in data if job_ids is None or d["job_id"] in job_ids]
        # print(json.dumps(data, indent=2))
        # return data
        
        query = f"""
            SELECT 
                job_id,
                gpu_type,
                {'hour,' if not aggregate else ''}
                {self._create_selector('vram_hours', aggregate)},
                {self._create_selector('cpu_hours', aggregate)},
                {self._create_selector('memory_hours', aggregate)}
            FROM logs.hourly_resource_usage_mv 
            WHERE user_id IN {tuple(user_ids)}
        """
        if job_ids is not None:
            query += f" AND job_id IN {tuple(job_ids)}"
        if start_time:
            query += f" AND hour >= '{start_time}'"
        if end_time:
            # Add one day to include all timestamps within the end_date
            end_date = datetime.strptime(end_time, "%Y-%m-%d") + timedelta(days=1)
            query += f" AND hour < '{end_date.strftime('%Y-%m-%d')}'"
        if aggregate:
            query += " GROUP BY job_id, gpu_type"
        else:
            query += " ORDER BY job_id, gpu_type, hour"
        result =  self._query(query)
        return result
    
    def get_provider_usage(
        self,
        provider_ids: list[str],
        start_time: str = None,
        end_time = None,
        aggregate: bool = True
    ):
        """
        Get compute usage metrics for a specific provider
        
        Args:
            provider_id (str): The provider ID to query
            start_time (str, optional): Start date for the query. Defaults to None.
            end_time (str, optional): End date for the query. Defaults to None.
            
        Returns:
            list: List of dictionaries containing usage metrics
        """
        query = f"""
            SELECT 
                provider,
                gpu_type,
                {'hour,' if not aggregate else ''}
                {self._create_selector('vram_hours', aggregate)},
                {self._create_selector('cpu_hours', aggregate)},
                {self._create_selector('memory_hours', aggregate)}
            FROM logs.hourly_resource_usage_mv 
            WHERE provider IN {tuple(provider_ids)}
        """
        if start_time:
            query += f" AND hour >= '{start_time}'"
        if end_time:
            # Add one day to include all timestamps within the end_date
            end_date = datetime.strptime(end_time, "%Y-%m-%d") + timedelta(days=1)
            query += f" AND hour < '{end_date.strftime('%Y-%m-%d')}'"
        if aggregate:
            query += " GROUP BY provider, gpu_type"
        else:
            query += " ORDER BY provider, gpu_type, hour"
        return self._query(query)


if __name__ == "__main__":
    metrics = MetricsAPI(
        endpoint=os.getenv("CLICKHOUSE_ENDPOINT", 'acmpvq21xs.europe-west2.gcp.clickhouse.cloud'),
        port=int(os.getenv("CLICKHOUSE_PORT", 8443)),
        username=os.getenv("CLICKHOUSE_USERNAME", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "NnhCZ97.fG2QI")
    )
    metrics.ping_service()
    data = metrics.get_compute_usage(
        user_ids=["user-1"],
        start_time="2026-05-26",
    )
    print(data)
    
    data = metrics.get_provider_usage(
        provider_ids=["nvidia"],
        start_time="2026-05-26",
    )
    print(data)
