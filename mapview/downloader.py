# coding=utf-8

__all__ = ["Downloader"]

from kivy.clock import Clock
from os.path import join, exists
from os import makedirs
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from random import choice
import requests
import traceback
from time import time
from mapview import CACHE_DIR


class Downloader(object):
    _instance = None
    MAX_WORKERS = 5
    CAP_TIME = 0.064  # 15 FPS

    @staticmethod
    def instance():
        if Downloader._instance is None:
            Downloader._instance = Downloader()
        return Downloader._instance

    def __init__(self, max_workers=None, cap_time=None):
        if max_workers is None:
            max_workers = Downloader.MAX_WORKERS
        if cap_time is None:
            cap_time = Downloader.CAP_TIME
        super(Downloader, self).__init__()
        self.is_paused = False
        self.cap_time = cap_time
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = []
        Clock.schedule_interval(self._check_executor, 1 / 60.)
        if not exists(CACHE_DIR):
            makedirs(CACHE_DIR)

    def submit(self, f, *args, **kwargs):
        future = self.executor.submit(f, *args, **kwargs)
        self._futures.append(future)

    def download_tile(self, tile):
        future = self.executor.submit(self._load_tile, tile)
        self._futures.append(future)

    def download(self, url, callback, **kwargs):
        future = self.executor.submit(self._download_url, url, callback, kwargs)
        self._futures.append(future)

    def _download_url(self, url, callback, kwargs):
        r = requests.get(url, **kwargs)
        return callback, (url, r, )

    def _load_tile(self, tile):
        if tile.state == "done":
            return
        cache_fn = tile.cache_fn
        if exists(cache_fn):
            return tile.set_source, (cache_fn, )
        tile_y = tile.map_source.get_row_count(tile.zoom) - tile.tile_y - 1
        uri = tile.map_source.url.format(z=tile.zoom, x=tile.tile_x, y=tile_y,
                              s=choice(tile.map_source.subdomains))
        #print "Download {}".format(uri)
        data = requests.get(uri, timeout=5).content
        with open(cache_fn, "wb") as fd:
            fd.write(data)
        #print "Downloaded {} bytes: {}".format(len(data), uri)
        return tile.set_source, (cache_fn, )

    def _check_executor(self, dt):
        start = time()
        try:
            for future in as_completed(self._futures[:], 0):
                self._futures.remove(future)
                try:
                    result = future.result()
                except:
                    traceback.print_exc()
                    # make an error tile?
                    continue
                if result is None:
                    continue
                callback, args = result
                callback(*args)

                # capped executor in time, in order to prevent too much slowiness.
                # seems to works quite great with big zoom-in/out
                if time() - start > self.cap_time:
                    break
        except TimeoutError:
            pass
