#!/usr/bin/python
#
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CredentialStore which stores Oauth token.

Exchanges long lived token for Oauth token
And also gets the token and gives user a link to login for Oauth flow
"""

import os
import os.path
from typing import Optional
from google.auth.exceptions import RefreshError
from google.auth.transport import requests
from google.oauth2 import credentials
from google_auth_oauthlib import flow
from utils import logger


SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.rolemanagement.readonly',
    'https://www.googleapis.com/auth/admin.directory.group.member',
    'https://www.googleapis.com/auth/admin.directory.group',
    'https://www.googleapis.com/auth/cloud-identity.groups',
    'https://www.googleapis.com/auth/admin.directory.orgunit',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/admin.directory.customer.readonly',
    'https://www.googleapis.com/auth/admin.directory.rolemanagement',
    'openid'
]
OA_TOKEN_FILE_NAME = 'oa-token.json'


class CredentialStore:
  """CredentialStore which stores Oauth token.

  Exchanges long lived token for Oauth token
  And also gets the token and gives user a link to login for Oauth flow
  """

  def __init__(self, output_path: str, oa_client_creds: str) -> None:
    self._output_path = output_path
    self._oa_client_id_creds = oa_client_creds
    self._token_path = os.path.join(self._output_path, OA_TOKEN_FILE_NAME)
    self._creds = None
    self.authenticate()

  def authenticate(self) -> None:
    """Authenticate by exchanging refresh token for oauth token.

    Or presenting the user with oauth consent link
    """
    if os.path.exists(self._token_path):
      self._creds = credentials.Credentials.from_authorized_user_file(
          self._token_path, SCOPES
      )

    # If there are no (valid) credentials available, let the user log in.
    if not self._creds or not self._creds.valid:
      if self._creds and self._creds.expired and self._creds.refresh_token:
        logger.Logger.get_instance().log(
            'Refreshing oauth-token at : {}.'.format(self._token_path)
        )
        try:
          self._creds.refresh(requests.Request())
        except RefreshError:
          self._present_oauth_consent_screen()
      else:
        self._present_oauth_consent_screen()

      # Save the credentials for the next run
      with open(self._token_path, 'w') as token:
        token.write(self._creds.to_json())

  def _present_oauth_consent_screen(self) -> None:
    logger.Logger.get_instance().log(
        'Presenting Oauth consent screen to obtain Oauth token.'
    )
    installed_flow = flow.InstalledAppFlow.from_client_secrets_file(
        self._oa_client_id_creds, SCOPES
    )
    self._creds = installed_flow.run_local_server(port=0, open_browser=False)

  def get_oauth_token(self) -> Optional[credentials.Credentials]:
    return self._creds
