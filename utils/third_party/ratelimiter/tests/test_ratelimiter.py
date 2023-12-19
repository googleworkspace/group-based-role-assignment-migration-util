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

import math
import random
import time
import unittest
import threading

from ratelimiter import RateLimiter


class Timer(object):

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop = time.time()
        self.duration = self.stop - self.start


class TestBasic(unittest.TestCase):

    period = 0.01
    max_calls = 10

    def setUp(self):
        random.seed()

    def validate_call_times(self, ts, max_calls, period):
        # Overall verification: total call duration should span over more than
        # the corresponding number of periods.
        timespan = math.ceil((ts[-1] - ts[0]) / period)
        self.assertGreaterEqual(max_calls, len(ts) / timespan)

        # Sliding verification: no group of 'max_calls' items should span over
        # less than a period.
        for i in range(len(ts) - max_calls):
            self.assertGreaterEqual(ts[i + max_calls] - ts[i], period)

    def test_bad_args(self):
        self.assertRaises(ValueError, RateLimiter, -1, self.period)
        self.assertRaises(ValueError, RateLimiter, +1, -self.period)

    def test_limit_1(self):
        with Timer() as timer:
            obj = RateLimiter(self.max_calls, self.period)
            for i in range(self.max_calls + 1):
                with obj:
                    # After the 'self.max_calls' iteration the execution
                    # inside the context manager should be blocked
                    # for the 'self.period' seconds.
                    pass
        # The sum of the time in the iterations without the rate limit blocking
        # is way lower than 'self.period'. If the duration of the all
        # iterations is greater or equal to the 'self.period' then blocking
        # and sleeping after the 'self.max_calls' iteration has been occured.
        self.assertGreaterEqual(timer.duration, self.period)

    def test_limit_2(self):
        calls = []
        obj = RateLimiter(self.max_calls, self.period)
        for i in range(3 * self.max_calls):
            with obj:
                calls.append(time.time())

        self.assertEqual(len(calls), 3 * self.max_calls)
        self.validate_call_times(calls, self.max_calls, self.period)

    def test_decorator_1(self):
        @RateLimiter(self.max_calls, self.period)
        def f():
            # After the 'self.max_calls' iteration the execution
            # of the function should be blocked for the 'self.period' seconds.
            pass

        with Timer() as timer:
            [f() for i in range(self.max_calls + 1)]

        # The sum of the time in the iterations without the rate limit blocking
        # is way lower than 'self.period'. If the duration of the all
        # iterations is greater or equal to the 'self.period' then blocking
        # and sleeping after the 'self.max_calls' iteration has been occured.
        self.assertGreaterEqual(timer.duration, self.period)

    def test_decorator_2(self):
        @RateLimiter(self.max_calls, self.period)
        def f():
            f.calls.append(time.time())
        f.calls = []

        [f() for i in range(3 * self.max_calls)]

        self.assertEqual(len(f.calls), 3 * self.max_calls)
        self.validate_call_times(f.calls, self.max_calls, self.period)

    def test_random(self):
        for _ in range(10):
            calls = []
            obj = RateLimiter(self.max_calls, self.period)
            for i in range(random.randint(10, 50)):
                with obj:
                    calls.append(time.time())

            self.validate_call_times(calls, self.max_calls, self.period)

    def test_threading(self):
        @RateLimiter(self.max_calls, self.period)
        def f():
            # After the 'self.max_calls' iteration the execution
            # of the function should be blocked for the 'self.period' seconds.
            pass

        with Timer() as timer:
            threads = []
            for i in range(self.max_calls + 1):
                # Running each target in it's own thread should not affect
                # the rate limiting
                t = threading.Thread(target=f)
                threads.append(t)
                t.start()
            [t.join() for t in threads]

        # The sum of the time in the iterations without the rate limit blocking
        # is way lower than 'self.period'. If the duration of the all
        # iterations is greater or equal to the 'self.period' then blocking
        # and sleeping after the 'self.max_calls' iteration has been occured.
        self.assertGreaterEqual(timer.duration, self.period)


if __name__ == "__main__":
    unittest.main()
