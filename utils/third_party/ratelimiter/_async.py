# -*- coding: utf-8 -*-
# Original work Copyright 2013 Arnaud Porterie
# Modified work Copyright 2016 Frazer McLean
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Async support for 3.5+ """

import time
import asyncio

from ._sync import RateLimiter


class AsyncRateLimiter(RateLimiter):

    def _init_async_lock(self):
        with self._init_lock:
            if self._alock is None:
                self._alock = asyncio.Lock()

    async def __aenter__(self):
        if self._alock is None:
            self._init_async_lock()

        async with self._alock:
            # We want to ensure that no more than max_calls were run in the allowed
            # period. For this, we store the last timestamps of each call and run
            # the rate verification upon each __enter__ call.
            if len(self.calls) >= self.max_calls:
                until = time.time() + self.period - self._timespan
                if self.callback:
                    asyncio.ensure_future(self.callback(until))
                sleeptime = until - time.time()
                if sleeptime > 0:
                    await asyncio.sleep(sleeptime)
            return self

    async def __aexit__(self, exc_type, exc_value, traceback):
         return super(AsyncRateLimiter, self).__exit__(exc_type, exc_value, traceback)
