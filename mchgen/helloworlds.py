#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) the Contributors as noted in the AUTHORS file.
from logzero import logger

def hello():
    logger.info("hello worlds!")
    return "hello worlds!"
