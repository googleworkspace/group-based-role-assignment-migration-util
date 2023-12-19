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

import sys

__author__ = 'Frazer McLean <frazer@frazermclean.co.uk>'
__version__ = '1.2.0.post0'
__license__ = 'Apache'
__description__ = 'Simple python rate limiting object'

# Async support is provided only on Python 3.5+
if sys.version_info >= (3, 5):
    from ._async import AsyncRateLimiter as RateLimiter
else:
    from ._sync import RateLimiter

__all__ = [
    "RateLimiter",
]
