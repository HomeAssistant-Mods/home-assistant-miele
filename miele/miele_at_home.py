import json
import logging

from datetime import timedelta

from requests.exceptions import ConnectionError
from requests_oauthlib import OAuth2Session

_LOGGER = logging.getLogger(__name__)

class MieleClient(object):
    DEVICES_URL = 'https://api.mcs3.miele.com/v1/devices'

    def __init__(self, session):
        self._session = session

    def _get_devices_raw(self, lang):
        _LOGGER.debug('Requesting Miele device update')
        try:
            devices = self._session._session.get(MieleClient.DEVICES_URL, params={'language':lang})
            if devices.status_code == 401:
                _LOGGER.info('Request unauthorized - attempting token refresh')
                if self._session.refresh_token():
                    return self._get_devices_raw(lang)    

            if devices.status_code != 200:
                _LOGGER.error('Failed to retrieve devices: {}'.format(devices.status_code))
                return None

            return devices.json()

        except ConnectionError as err:
             _LOGGER.error('Failed to retrieve Miele devices: {0}'.format(err))
             return None

    def get_devices(self, lang='en'):
        home_devices = self._get_devices_raw(lang)
        if home_devices is None:
            return None

        result = []
        for home_device in home_devices:
            result.append(home_devices[home_device])

        return result   

    def get_device(self, device_id, lang='en'):
        devices = self._get_devices_raw(lang)
        if devices is None:
            return None

        if devices is not None:
            return devices[device_id]

        return None


class MieleOAuth(object):
    '''
    Implements Authorization Code Flow for Miele@home implementation.
    '''

    OAUTH_AUTHORIZE_URL = 'https://api.mcs3.miele.com/thirdparty/login'
    OAUTH_TOKEN_URL = 'https://api.mcs3.miele.com/thirdparty/token'

    def __init__(self, client_id, client_secret, redirect_uri, cache_path=None):
        self._client_id = client_id
        self._client_secret = client_secret
        self._cache_path = cache_path

        self._token = self._get_cached_token()

        self._session = OAuth2Session(self._client_id,
            auto_refresh_url=MieleOAuth.OAUTH_TOKEN_URL,
            redirect_uri=redirect_uri, 
            token=self._token, 
            token_updater=self._save_token)

        if self.authorized:
            self.refresh_token()

    @property
    def authorized(self):
        return self._session.authorized

    @property
    def authorization_url(self):
        return self._session.authorization_url(MieleOAuth.OAUTH_AUTHORIZE_URL, state='login')[0]
        
        
    def get_access_token(self, client_code):
        token = self._session.fetch_token(
            MieleOAuth.OAUTH_TOKEN_URL,
            code=client_code,
            include_client_id=True,
            client_secret=self._client_secret)
        self._save_token(token)

        return token

    def refresh_token(self):
        body = 'client_id={}&client_secret={}&'.format(self._client_id, self._client_secret)
        self._token = self._session.refresh_token(MieleOAuth.OAUTH_TOKEN_URL,
            body=body,
            refresh_token=self._token['refresh_token'])
        self._save_token(self._token)
            
    def _get_cached_token(self):
        token = None
        if self._cache_path:
            try:
                f = open(self._cache_path)
                token_info_string = f.read()
                f.close()
                token = json.loads(token_info_string)

            except IOError:
                pass
        
        return token

    def _save_token(self, token):
        if self._cache_path:
            try:
                f = open(self._cache_path, 'w')
                f.write(json.dumps(token))
                f.close()
            except IOError:
                _LOGGER._warn('Couldn\'t write token cache to {0}'.format(self._cache_path))
                pass
