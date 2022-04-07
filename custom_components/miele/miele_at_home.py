import functools
import json
import logging
import os
from datetime import timedelta

from requests.exceptions import ConnectionError
from requests_oauthlib import OAuth2Session

_LOGGER = logging.getLogger(__name__)


class MieleClient(object):
    DEVICES_URL = "https://api.mcs3.miele.com/v1/devices"
    ACTION_URL = "https://api.mcs3.miele.com/v1/devices/{0}/actions"

    def __init__(self, hass, session):
        self._session = session
        self.hass = hass

    async def _get_devices_raw(self, lang):
        _LOGGER.debug("Requesting Miele device update")
        try:
            func = functools.partial(
                self._session._session.get,
                MieleClient.DEVICES_URL,
                params={"language": lang},
            )
            devices = await self.hass.async_add_executor_job(func)
            if devices.status_code == 401:
                _LOGGER.info("Request unauthorized - attempting token refresh")
                if await self._session.refresh_token(self.hass):
                    return await self._get_devices_raw(lang)

            if devices.status_code != 200:
                _LOGGER.debug(
                    "Failed to retrieve devices: {}".format(devices.status_code)
                )
                return None

            return devices.json()

        except ConnectionError as err:
            _LOGGER.error("Failed to retrieve Miele devices: {0}".format(err))
            return None

    async def get_devices(self, lang="en"):
        home_devices = await self._get_devices_raw(lang)
        if home_devices is None:
            return None

        result = []
        for home_device in home_devices:
            result.append(home_devices[home_device])

        return result

    def get_device(self, device_id, lang="en"):
        devices = self._get_devices_raw(lang)
        if devices is None:
            return None

        if devices is not None:
            return devices[device_id]

        return None

    async def action(self, device_id, body):
        _LOGGER.debug("Executing device action for {}{}".format(device_id, body))
        try:
            headers = {"Content-Type": "application/json"}
            func = functools.partial(
                self._session._session.put,
                MieleClient.ACTION_URL.format(device_id),
                data=json.dumps(body),
                headers=headers,
            )
            result = await self.hass.async_add_executor_job(func)
            if result.status_code == 401:
                _LOGGER.info("Request unauthorized - attempting token refresh")

                if await self._session.refresh_token(self.hass):
                    if self._session.authorized:
                        return self.action(device_id, body)
                    else:
                        self._session._delete_token()
                        self._session.new_session()
                        return self.action(device_id, body)

            if result.status_code == 200:
                return result.json()
            elif result.status_code == 204:
                return None
            else:
                _LOGGER.error(
                    "Failed to execute device action for {}: {} {}".format(
                        device_id, result.status_code, result.json()
                    )
                )
                return None

        except ConnectionError as err:
            _LOGGER.error("Failed to execute device action: {}".format(err))
            return None


class MieleOAuth(object):
    """
    Implements Authorization Code Flow for Miele@home implementation.
    """

    OAUTH_AUTHORIZE_URL = "https://api.mcs3.miele.com/thirdparty/login"
    OAUTH_TOKEN_URL = "https://api.mcs3.miele.com/thirdparty/token"

    def __init__(self, hass, client_id, client_secret, redirect_uri, cache_path=None):
        self._client_id = client_id
        self._client_secret = client_secret
        self._cache_path = cache_path
        self._redirect_uri = redirect_uri

        self._token = self._get_cached_token()

        self._extra = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        self._session = OAuth2Session(
            self._client_id,
            auto_refresh_url=MieleOAuth.OAUTH_TOKEN_URL,
            redirect_uri=redirect_uri,
            token=self._token,
            token_updater=self._save_token,
            auto_refresh_kwargs=self._extra,
        )

        if self.authorized:
            self.refresh_token(hass)

    @property
    def authorized(self):
        return self._session.authorized

    @property
    def authorization_url(self):
        return self._session.authorization_url(
            MieleOAuth.OAUTH_AUTHORIZE_URL, state="login"
        )[0]

    def get_access_token(self, client_code):
        token = self._session.fetch_token(
            MieleOAuth.OAUTH_TOKEN_URL,
            code=client_code,
            include_client_id=True,
            client_secret=self._client_secret,
        )
        self._save_token(token)

        return token

    async def refresh_token(self, hass):
        body = "client_id={}&client_secret={}&".format(
            self._client_id, self._client_secret
        )
        self._token = await hass.async_add_executor_job(
            self.sync_refresh_token,
            MieleOAuth.OAUTH_TOKEN_URL,
            body,
            self._token["refresh_token"],
        )
        self._save_token(self._token)

    def sync_refresh_token(self, token_url, body, refresh_token):
        return self._session.refresh_token(
            token_url, body=body, refresh_token=refresh_token
        )

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

    def _delete_token(self):
        if self._cache_path:
            try:
                os.remove(self._cache_path)

            except IOError:
                _LOGGER.warn("Unable to delete cached token")

        self._token = None

    def _new_session(self, redirect_uri):
        self._session = OAuth2Session(
            self._client_id,
            auto_refresh_url=MieleOAuth.OAUTH_TOKEN_URL,
            redirect_uri=self._redirect_uri,
            token=self._token,
            token_updater=self._save_token,
            auto_refresh_kwargs=self._extra,
        )

        if self.authorized:
            self.refresh_token()

    def _save_token(self, token):
        _LOGGER.debug("trying to save new token")
        if self._cache_path:
            try:
                f = open(self._cache_path, "w")
                f.write(json.dumps(token))
                f.close()
            except IOError:
                _LOGGER._warn(
                    "Couldn't write token cache to {0}".format(self._cache_path)
                )
                pass

        self._token = token
