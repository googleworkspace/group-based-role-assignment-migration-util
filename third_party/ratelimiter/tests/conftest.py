#!/usr/bin/python
# coding: utf-8
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

from __future__ import absolute_import, division, print_function

import sys

import pytest


class DummyCollector(pytest.File):
    def collect(self):
        return []


def pytest_pycollect_makemodule(path, parent):
    # skip asyncio tests unless on Python 3.5+, because async/await
    # is a SyntaxError.
    if 'aio' in path.basename and sys.version_info < (3, 5):
        return DummyCollector(path, parent=parent)
