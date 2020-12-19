Python Client for SPYPOINT Cloud API
====================================

This is an unofficial client for the [SPYPOINT](https://www.spypoint.com) Cloud API. You can use it to obtain download
urls for recent photos uploaded by your cellular trail camera.

Usage
-----

```python
import spypoint
c = spypoint.Client(username, password)
[p.url() for p in c.photos(c.cameras(), limit=1)]
```
