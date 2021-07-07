# Copyright (c) 2020 by Henry Stern
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Collection, Dict, List

import requests

from .exceptions import *

API_BASE = 'https://restapi.spypoint.com'
LOGIN_URL = f'{API_BASE}/api/v3/user/login'
CAMERA_URL = f'{API_BASE}/api/v3/camera/all'
PHOTO_URL = f'{API_BASE}/api/v3/photo/all'
FILTERS_URL = f'{API_BASE}/api/v3/photo/filters'


class _AttrDict:
    def __init__(self, d):  # noqa
        for k, v in d.items():
            if isinstance(v, Dict):
                v = _AttrDict(v)
            elif isinstance(v, List):
                v_new = list()
                for v_sub in v:
                    if isinstance(v_sub, dict):
                        v_new.append(_AttrDict(v_sub))
                    else:
                        v_new.append(v_sub)
                v = tuple(v_new)
            if k and k[0] != '_':
                setattr(self, k, v)


class Camera(_AttrDict):
    def __init__(self, id, **kwargs):  # noqa
        super(Camera, self).__init__(kwargs)
        self.id = id

    def __repr__(self):
        return f'Camera({self.id})'


class Photo(_AttrDict):
    def __init__(self, **kwargs):
        super(Photo, self).__init__(kwargs)

    def __repr__(self):
        return f'Photo({self.id})'  # noqa

    def url(self, size='large'):
        section = getattr(self, size, dict())
        return f'https://{getattr(section, "host")}/{getattr(section, "path")}'


class Client:
    def __init__(self, username: str, password: str, session: requests.Session = None) -> None:
        self.username = username
        self.password = password
        self.uid = ''
        self.token = ''
        if session:
            self.session = session
        else:
            self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        res = {
            'accept': 'application/json',
        }
        if self.uid:
            res['authorization'] = f'Bearer {self.token}'
        return res

    @catches
    def login(self, force: bool = False) -> None:
        if force or not self.uid:
            res = self.session.post(LOGIN_URL, headers={
                'accept': 'application/json',
            }, json={
                'username': self.username,
                'password': self.password,
            })
            res.raise_for_status()
            body = res.json()

            self.uid = body['uuid']
            self.token = body['token']

    @catches
    def cameras(self) -> Collection[Camera]:
        self.login()
        res = self.session.get(CAMERA_URL, headers=self._headers())
        res.raise_for_status()
        return [Camera(**camera) for camera in res.json()]

    @catches
    def photos(self, cameras: Collection[Camera],
               date_end: str = "2100-01-01T00:00:00.000Z",
               hd: bool = False,
               favorite: bool = False,
               limit: int = 100,
               tags: Collection[str] = tuple())\
            -> Collection[Photo]:

        self.login()
        res = self.session.post(PHOTO_URL, headers=self._headers(), json={
            'camera': [camera.id for camera in cameras],
            'dateEnd': date_end,
            'favorite': favorite,
            'hd': hd,
            'limit': limit,
            'tag': list(tags),
        })
        res.raise_for_status()
        return [Photo(**photo) for photo in res.json().get('photos', [])]

    @catches
    def tags(self) -> Collection[str]:
        self.login()
        res = self.session.get(FILTERS_URL, headers=self._headers())
        res.raise_for_status()
        return [x.get('nameId') for x in res.json().get('species', [])]
