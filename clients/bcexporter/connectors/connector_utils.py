from appmetrics.AppMetrics import AppMetrics
from connectors.AvaxConnector import AvaxConnector
from connectors.ChainUrl import ChainUrl
from connectors.EthConnector import EthConnector
from data.AvaxChainID import AvaxChainID
from data.PoktChainID import PoktChainID


def create_connectors(appmetrics: AppMetrics, chains) -> list:
    connectors = []
    for chain in chains:
        chain_url_obj = ChainUrl(chain["url"])
        if chain["id"] == PoktChainID.SWIMMER:
            connectors.append(AvaxConnector(chain_url_obj=chain_url_obj, destination=appmetrics, id=chain["id"],
                                            chain=AvaxChainID.SWIMMER))

        elif chain["id"] == PoktChainID.AVAX:
            [connectors.append(
                AvaxConnector(chain_url_obj=chain_url_obj, destination=appmetrics, id=chain["id"], chain=subnet))
                for subnet in ["P", "X", "C"]]

        elif chain["id"] == PoktChainID.DFK:
            connectors.append(AvaxConnector(chain_url_obj=chain_url_obj, destination=appmetrics, id=chain["id"],
                                            chain=AvaxChainID.DFK))
        else:
            connectors.append(EthConnector(chain_url_obj=chain_url_obj, destination=appmetrics, id=chain["id"]))

    return connectors
