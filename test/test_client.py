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

import json
import unittest

import requests
import requests_mock

import spypoint.client as c


@requests_mock.Mocker()
class TestClient(unittest.TestCase):
    username = 'elided@example.com'
    password = 'RXFqK3cJVPetEgqwP9w*'
    uid = 'elided00'
    token = 'rjREK-49kA7yM*Q6JiRe'

    camera_tdata = json.loads('''
        [
          {
            "id": "elided01"
          }
        ]
    ''')

    photo_tdata = json.loads('''
        {
          "photos": [
            {
              "id": "elided01"
            },
            {
              "id": "elided02"
            }
          ]
        }    
    ''')

    tags_tdata = json.loads('''
        {
          "species": [
            {
              "nameId": "buck",
              "iconUrl": "https://s3.amazonaws.com/spypoint-static-assets/filters/buck.png"
            },
            {
              "nameId": "deer",
              "iconUrl": "https://s3.amazonaws.com/spypoint-static-assets/filters/deer.png"
            }
          ]
        }
    ''')

    def setUp(self):
        self.client = c.Client(self.username, self.password)

    def _header_matcher(self, request: requests.Request):
        bearer, token = request.headers['Authorization'].split(' ', 1)
        return bearer.lower() == 'bearer' and token == self.token

    def _login_matcher(self, request: requests.Request):
        for k, v in {
            'username': self.username,
            'password': self.password,
        }.items():
            if request.json()[k] != v:
                return False
        return True

    def _login_request(self, m: requests_mock.Mocker):
        m.post(c.LOGIN_URL,
               additional_matcher=self._login_matcher,
               json={
                   'uuid': self.uid,
                   'token': self.token,
               })

    def _check_logged_in(self):
        self.assertEqual(self.uid, self.client.uid)
        self.assertEqual(self.token, self.client.token)

    def test_login(self, m: requests_mock.Mocker):
        self._login_request(m)

        self.assertEqual('', self.client.uid)
        self.assertEqual('', self.client.token)
        self.client.login()
        self._check_logged_in()

    def test_cameras(self, m: requests_mock.Mocker):
        self._login_request(m)

        m.get(c.CAMERA_URL, additional_matcher=self._header_matcher, json=self.camera_tdata)

        self.assertEqual(
            [camera['id'] for camera in self.camera_tdata],
            [camera.id for camera in self.client.cameras()],
        )
        self._check_logged_in()

    def test_photos(self, m: requests_mock.Mocker):
        camera_id = 'elided01'

        def photo_matcher(request: requests.Request):
            if not self._header_matcher(request):
                return False
            return set(request.json()['camera']) == {camera_id}

        self._login_request(m)

        m.post(c.PHOTO_URL, additional_matcher=photo_matcher, json=self.photo_tdata)

        self.assertEqual(
            [photo['id'] for photo in self.photo_tdata.get('photos')],
            [photo.id for photo in self.client.photos(cameras=[c.Camera(camera_id)])],  # noqa
        )
        self._check_logged_in()

    def test_tags(self, m: requests_mock.Mocker):
        self._login_request(m)

        m.get(c.FILTERS_URL, additional_matcher=self._header_matcher, json=self.tags_tdata)

        self.assertSetEqual(
            set(tag['nameId'] for tag in self.tags_tdata['species']),
            set(self.client.tags()),
        )
        self._check_logged_in()


class TestCamera(unittest.TestCase):
    tdata = json.loads('''
        {
          "id": "elided01",
          "status": "test_status",
          "config": {
            "name": "test_camera"
          }
        }
    ''')

    def test_camera(self):
        camera = c.Camera(**self.tdata)
        self.assertEqual(self.tdata['id'], camera.id)
        self.assertEqual(self.tdata['status'], camera.status)
        self.assertEqual(self.tdata['config']['name'], camera.config.name)


class TestPhoto(unittest.TestCase):
    tdata = json.loads('''
        {
          "id": "elided02",
          "date": "2020-12-18T01:00:00.000Z",
          "tag": [
            "deer",
            "night"
          ],
          "originName": "PICT0001.JPG",
          "originSize": 12345,
          "originDate": "2020-12-18T00:00:00.000Z",
          "small": {
            "verb": "GET",
            "path": "spypoint-production-account/elided00/elided01/20201218/PICT0001_S_2020121800000yQlv.jpg?X-Amz-Expires=86400&X-Amz-Date=20201218T212548Z&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIATVANQEDJ5KPEZXK2%2F20201218%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-SignedHeaders=host&X-Amz-Signature=elided",
            "host": "s3.amazonaws.com",
            "headers": [
              {
                "name": "Content-Type",
                "value": "image/jpeg"
              }
            ]
          },
          "medium": {
            "verb": "GET",
            "path": "spypoint-production-account/elided00/elided01/20201218/PICT0001_M_2020121800000yQlv.jpg?X-Amz-Expires=86400&X-Amz-Date=20201218T212548Z&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIATVANQEDJ5KPEZXK2%2F20201218%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-SignedHeaders=host&X-Amz-Signature=elided",
            "host": "s3.amazonaws.com",
            "headers": [
              {
                "name": "Content-Type",
                "value": "image/jpeg"
              }
            ]
          },
          "large": {
            "verb": "GET",
            "path": "spypoint-production-account/elided00/elided01/20201218/PICT0001_2020121800000yQlv.jpg?X-Amz-Expires=86400&X-Amz-Date=20201218T212548Z&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ELIDED%2F20201218%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-SignedHeaders=host&X-Amz-Signature=elided",
            "host": "s3.amazonaws.com",
            "headers": [
              {
                "name": "Content-Type",
                "value": "image/jpeg"
              }
            ]
          },
          "camera": "elided01",
          "hd": {
            "verb": "",
            "path": "",
            "host": "",
            "headers": []
          }
        }
    ''')  # noqa

    def test_url_small(self):
        self._test_url('small')

    def test_url_medium(self):
        self._test_url('medium')

    def test_url_large(self):
        self._test_url('large')

    def _test_url(self, size):
        p = c.Photo(**self.tdata)
        self.assertEqual(self.tdata['small']['headers'][0]['name'], p.small.headers[0].name)
        self.assertEqual(f'https://s3.amazonaws.com/{self.tdata[size]["path"]}', p.url(size))
