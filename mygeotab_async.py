# -*- coding: utf-8 -*-

import asyncio
import json

import aiohttp

import mygeotab
import mygeotab.serializers


class AsyncAPI(mygeotab.API):
    def __init__(self, username, password=None, database=None, session_id=None, server='my.geotab.com'):
        """
        Creates a new instance of this simple Pythonic wrapper for the MyGeotab API.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :param session_id: A session ID, assigned by the server.
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """
        super().__init__(username, password, database, session_id, server)

    @asyncio.coroutine
    def _query(self, method, parameters):
        """
        Formats and performs the query against the API

        :param method: The method name.
        :param parameters: A dict of parameters to send
        :return: The JSON-decoded result from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        params = dict(id=-1, method=method, params=parameters)
        headers = {'Content-type': 'application/json; charset=UTF-8'}
        r = yield from aiohttp.post(self._api_url,
                                    data=json.dumps(params,
                                                    default=mygeotab.serializers.object_serializer),
                                    headers=headers,
                                    allow_redirects=True)
        body = yield from r.text()
        return self._process(json.loads(body, object_hook=mygeotab.serializers.object_deserializer))

    @asyncio.coroutine
    def call(self, method, type_name=None, **parameters):
        """
        Makes a call to the API.

        :param method: The method name.
        :param type_name: The type of entity for generic methods (for example, 'Get')
        :param parameters: Additional parameters to send (for example, search=dict(id='b123') )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if method is None:
            raise Exception("Must specify a method name")
        if parameters is None:
            parameters = {}
        if type_name:
            parameters['typeName'] = type_name
        if self.credentials is None:
            yield from self.authenticate()
        if 'credentials' not in parameters and self.credentials.session_id:
            parameters['credentials'] = self.credentials.get_param()

        try:
            result = yield from self._query(method, parameters)
            if result is not None:
                self._reauthorize_count = 0
                return result
        except mygeotab.MyGeotabException as exception:
            if exception.name == 'InvalidUserException' and self._reauthorize_count == 0:
                self._reauthorize_count += 1
                yield from self.authenticate()
                return (yield from self.call(method, parameters))
            raise
        return None

    @asyncio.coroutine
    def multi_call(self, *calls):
        """
        Performs a multi-call to the API

        :param calls: A list of call 2-tuples with method name and params (for example, ('Get', dict(typeName='Trip')) )
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        formatted_calls = [dict(method=call[0], params=call[1]) for call in calls]
        return (yield from self.call('ExecuteMultiCall', calls=formatted_calls))

    @asyncio.coroutine
    def get(self, type_name, **parameters):
        """
        Gets entities using the API. Shortcut for using call() with the 'Get' method.

        :param type_name: The type of entity
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return (yield from self.call('Get', type_name, **parameters))

    @asyncio.coroutine
    def search(self, type_name, **parameters):
        """
        Searches for entities using the API. Shortcut for using get() with a search.

        :param type_name: The type of entity
        :param parameters: Additional parameters to send.
        :return: The JSON result (decoded into a dict) from the server
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        if parameters:
            results_limit = parameters.get('resultsLimit', None)
            if results_limit is not None:
                del parameters['resultsLimit']
            parameters = dict(search=parameters)
            return (yield from self.call('Get', type_name, resultsLimit=results_limit, **parameters))
        return (yield from self.get(type_name))

    @asyncio.coroutine
    def add(self, type_name, entity):
        """
        Adds an entity using the API. Shortcut for using call() with the 'Add' method.

        :param type_name: The type of entity
        :param entity: The entity to add
        :return: The id of the object added
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return (yield from self.call('Add', type_name, entity=entity))

    @asyncio.coroutine
    def set(self, type_name, entity):
        """
        Sets an entity using the API. Shortcut for using call() with the 'Set' method.

        :param type_name: The type of entity
        :param entity: The entity to set
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return (yield from self.call('Set', type_name, entity=entity))

    @asyncio.coroutine
    def remove(self, type_name, entity):
        """
        Removes an entity using the API. Shortcut for using call() with the 'Remove' method.

        :param type_name: The type of entity
        :param entity: The entity to remove
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        return (yield from self.call('Remove', type_name, entity=entity))

    @asyncio.coroutine
    def authenticate(self):
        """
        Authenticates against the API server.

        :return: A Credentials object with a session ID created by the server
        :raise AuthenticationException: Raises if there was an issue with authenticating or logging in
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server
        """
        auth_data = dict(database=self.credentials.database, userName=self.credentials.username,
                         password=self.credentials.password)
        auth_data['global'] = True
        try:
            result = yield from self._query('Authenticate', auth_data)
            if result:
                new_server = result['path']
                server = self.credentials.server
                if new_server != 'ThisServer':
                    server = new_server
                c = result['credentials']
                self.credentials = mygeotab.Credentials(c['userName'], c['sessionId'], c['database'],
                                               server)
                return self.credentials
        except mygeotab.MyGeotabException as exception:
            if exception.name == 'InvalidUserException':
                raise mygeotab.AuthenticationException(self.credentials.username,
                                              self.credentials.database,
                                              self.credentials.server)
            raise

__title__ = 'mygeotab-async'
__author__ = 'Aaron Toth'
__version__ = '0.1'