#!/usr/bin/python
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

import pytest

from ratelimiter import RateLimiter

@pytest.mark.asyncio
async def test_alock(event_loop):
    rl = RateLimiter(max_calls=10, period=0.01)

    assert rl._alock is None

    async with rl:
        pass

    alock = rl._alock
    assert alock

    async with rl:
        pass

    assert rl._alock is alock
