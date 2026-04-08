import requests
import json


class APIUntilities(object):
    """Utility class for API interactions."""

    def __init__(self, api_data, logger):
        self.__api_data = api_data
        self.__logger = logger
        self.__client_id = api_data.get('client_id', '')
        self.__client_secret = api_data.get('client_secret', '')
        self.__user_uuid = api_data.get('user_uuid', '')
        self.__token_url = api_data.get('token_url', '')

    def get_access_token_with_uuid(self):
        """
        Fetches an access token from an API using client credentials and a UUID.
        """
        
        # Payload data required by the API
        payload = {
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'uuid': self.__user_uuid,
            # Other potential parameters like 'grant_type' may be needed
            'grant_type': 'client_credentials' 
        }
        
        # Headers for the request
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            # Make the POST request to the token endpoint
            response = requests.post(self.__token_url, headers=headers, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            # Parse the JSON response
            token_data = response.json()
            
            # Extract the access token
            access_token = token_data.get('access_token')
            
            if access_token:
                return access_token
            else:
                self.__logger.info("Error: 'access_token' not found in response.")
                return None
                
        except requests.exceptions.RequestException as e:
            self.__logger.error(f"Request error: {e}")
            return None

