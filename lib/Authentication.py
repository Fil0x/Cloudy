import json
import httplib2

import local
import logger
import faults
from DataManager import Manager
from DataManager import LocalDataManager

from kamaki.clients import ClientError
from astakosclient import AstakosClient
from astakosclient import errors as AstakosErrors
from lib.CloudyPithosClient import CloudyPithosClient
from dropbox import rest
from dropbox.client import DropboxClient
from dropbox.client import DropboxOAuth2FlowNoRedirect
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import AccessTokenRefreshError

class PithosFlow(object):
    def start(self):
        return local.Pithos_LOGINURL

    def finish(self, token):
        s = AstakosClient(local.Pithos_AUTHURL, logger=logger.logger_factory('astakosclient'))
        s.get_endpoints(token)
        return token

class GoogleDriveFlowWrapper(object):
    def __init__(self, flow):
        self.flow = flow

    def start(self):
        return self.flow.step1_get_authorize_url()

    def finish(self, code):
        return self.flow.step2_exchange(code)
        
class AuthManager(Manager):
    def __init__(self):
        self.auth_functions = [self._dropbox_auth,
                               self._pithos_auth,
                               self._googledrive_auth]
        self.service_auth = dict(zip(self.services, self.auth_functions))

        self.add_functions = [self._dropbox_add_user,
                              self._pithos_add_user,
                              self._googledrive_add_user]
        self.add_user = dict(zip(self.services, self.add_functions))

    #exposed functions
    def authenticate(self, service):
        assert(service in self.services)

        return self.service_auth[service]()

    def add_and_authenticate(self, service, key):
        assert(service in self.services)

        return self.add_user[service](key)

    def get_flow(self, service):
        assert(service in self.services)

        return getattr(self, '_get_{}_flow'.format(service.lower()))()

    #end of exposed functions
    def _call_exceptional(self, client, create=False):
        try:
            client.get_container_info() if not create else \
            client.create_container()
        except ClientError as e:
            if e.status == 401:
                raise faults.InvalidAuth('Pithos-Auth')
            elif 'Errno 11004' in e.message:
                raise faults.NetworkError('No internet-Auth')
            elif e.status == 404:
                self._call_exceptional(client, True)
        
    def _pithos_auth(self):
        access_token = None
        dataManager = LocalDataManager()
        
        #A KeyError will be raised if there is no token.
        access_token = dataManager.get_credentials('Pithos')
        
        try:
            dm = LocalDataManager()
            s = AstakosClient(local.Pithos_AUTHURL)
            pithos_url = self._get_pithos_public_url(s.get_endpoints(access_token))
            uuid = s.get_user_info(access_token)['uuid']
            pithosClient = CloudyPithosClient(pithos_url, access_token, uuid)
            pithosClient.container = dm.get_service_root('Pithos')
            
            #Check if the container saved in the settings exists.
            self._call_exceptional(pithosClient)
        except (AstakosErrors.Unauthorized, faults.InvalidAuth) as e:
            raise faults.InvalidAuth('Pithos-Auth')
        except (AstakosErrors.AstakosClientException, faults.NetworkError) as e:
            raise faults.NetworkError('No internet-Auth')
        
        return pithosClient

    def _pithos_add_user(self, key):
        dataManager = LocalDataManager()
        dataManager.set_credentials('Pithos', key)
        return self._pithos_auth()

    #https://www.dropbox.com/developers/core/docs/error handling
    def _dropbox_auth(self):
        access_token = None
        dataManager = LocalDataManager()

        #A KeyError will be raised if there is no token.
        access_token = dataManager.get_credentials('Dropbox')

        dropboxClient = DropboxClient(access_token)

        try:
            dropboxClient.account_info()
        except rest.ErrorResponse as e:
            if e.status == 401:
                raise faults.InvalidAuth('Dropbox-Auth')
        except rest.RESTSocketError as e:
            raise faults.NetworkError('No internet-Auth')

        return dropboxClient

    def _dropbox_add_user(self, key):
        dataManager = LocalDataManager()
        dataManager.set_credentials('Dropbox', key)
        return self._dropbox_auth()

    #http://tinyurl.com/kdv3ttb
    def _googledrive_auth(self):
        credentials = None
        dataManager = LocalDataManager()

        #A KeyError will be raised if there is no token.
        credentials = dataManager.get_credentials('GoogleDrive')

        credentials = Credentials.new_from_json(credentials)
        http = credentials.authorize(httplib2.Http())
        try:
            drive_service = build('drive', 'v2', http=http)
        except httplib2.ServerNotFoundError:
            raise faults.NetworkError('No internet.')

        try:
            drive_service.about().get().execute()
        except errors.HttpError as e:
            raise
        except AccessTokenRefreshError:
            raise faults.InvalidAuth('GoogleDrive')

        dataManager.set_credentials('GoogleDrive', credentials)
        return drive_service

    def _googledrive_add_user(self, credentials):
        dataManager = LocalDataManager()
        dataManager.set_credentials('GoogleDrive', credentials)
        return self._googledrive_auth()

    def _get_dropbox_flow(self):
        return DropboxOAuth2FlowNoRedirect(local.Dropbox_APPKEY,
                                           local.Dropbox_APPSECRET)

    def _get_googledrive_flow(self):
        flow = OAuth2WebServerFlow(local.GoogleDrive_APPKEY, local.GoogleDrive_APPSECRET,
                                   local.GoogleDrive_OAUTHSCOPE, local.GoogleDrive_REDIRECTURI)
        return GoogleDriveFlowWrapper(flow)

    def _get_pithos_flow(self):
        return PithosFlow()

    def _get_pithos_public_url(self, endpoints, type=u'object-store'):
        r = endpoints[u'access'][u'serviceCatalog']
        for i in r:
            if i[u'type'] == type:
                return i[u'endpoints'][0][u'publicURL']
        return None
