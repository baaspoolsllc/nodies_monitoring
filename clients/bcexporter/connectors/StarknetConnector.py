import asyncio
import json
import traceback
import urllib.parse

import aiohttp

from appmetrics.AppMetrics import AppMetrics
from connectors.ChainUrl import ChainUrl
from connectors.Web3Connector import Web3Connector
from data.ChainSyncStatus import ChainSyncStatus


class StarknetConnector(Web3Connector):

    def __init__(self, chain_url_obj: ChainUrl, destination: AppMetrics, id: str, request_kwargs=None):
        self.id = id
        self.chain_url_obj = chain_url_obj
        self.labels = [id, str(chain_url_obj)]
        self.destination = destination

    async def get_sync_data(self) -> dict:
        # Returns dict if currently syncing, otherwise returns False
        async with aiohttp.ClientSession() as async_session:
            response = await async_session.post(
                timeout=5,
                url=self.chain_url_obj.get_endpoint(),
                json={
                    "jsonrpc": "2.0",
                    "id": "67",
                    "method": "starknet_syncing",
                    "params": []
                },
                headers={"content-type": "application/json"}
            )
            json_object = json.loads((await response.content.read()).decode("utf8"))
            sync_info = json_object["result"]#["sync_info"]
            sync_dict = {
                "current_block": int(sync_info["current_block_num"], 16),
                "latest_block": int(sync_info["highest_block_num"], 16),
                "status": ChainSyncStatus.SYNCING if sync_info["current_block_num"] != sync_info["highest_block_num"] else ChainSyncStatus.SYNCED
            }
            return sync_dict

    async def get_current_block(self) -> int:
        return -1

    async def get_latest_block(self) -> int:
        """
        Latest block is same as current block whenever node is synced.
        We can later replace this with a value from an explorer or an altruist if needed.
        """
        return await self.get_current_block()

    async def report_metrics(self):
        """
        Get metrics from node and refresh Prometheus metrics with
        new values.
        """
        try:
            sync_data = await self.get_sync_data()
            curr_height = sync_data["current_block"]
            latest_height = sync_data["latest_block"]
            self.destination.curr_height.labels(*self.labels).set(curr_height)
            self.destination.latest_height.labels(*self.labels).set(latest_height)
            self.destination.sync_status.labels(*self.labels).set(sync_data["status"])
            print(f"{self.chain_url_obj.get_endpoint()} sent metrics for chain {self.id}")
            print(f'Status: {sync_data["status"]}\nCurrent Height: {curr_height}\nLatest Height: {latest_height}')
        except (asyncio.TimeoutError) as e:
            print(f'Timeout Exception with: {self.chain_url_obj.get_endpoint()}')
            traceback.print_exc()
            self.destination.sync_status.labels(*self.labels).set(ChainSyncStatus.STOPPED)
            self.destination.curr_height.labels(*self.labels).set(0)
            self.destination.latest_height.labels(*self.labels).set(0)
        except Exception as e:
            print(f'Exception with: {self.chain_url_obj.get_endpoint()}')
            traceback.print_exc()
            #temporary until graphs can handle UNKNOWN
            self.destination.sync_status.labels(*self.labels).set(ChainSyncStatus.STOPPED)
            self.destination.curr_height.labels(*self.labels).set(0)
            self.destination.latest_height.labels(*self.labels).set(0)

