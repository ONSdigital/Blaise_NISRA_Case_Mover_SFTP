import logging
from typing import List, Dict, Any

import blaise_restapi

from models.configuration.blaise_config_model import BlaiseConfig


class BlaiseService:
    def __init__(self, config: BlaiseConfig):
        self._config = config
        self.restapi_client = blaise_restapi.Client(f"http://{self._config.blaise_api_url}")

    def get_questionnaires(self) -> List[Dict[str, Any]]:
        try:
            return self.restapi_client.get_all_questionnaires_for_server_park(self._config.server_park)
        except Exception as error:
            logging.error("BlaiseService: error in calling 'get_all_questionnaires_for_server_park'", error)
