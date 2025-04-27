# SPDX-License-Identifier: Apache-2.0

# Copyright (c) 2025 Pluraf Embedded AB <code@pluraf.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import time
import enum

from app.database_setup import DefaultBase
from sqlalchemy import Column, String, Integer


class ApitokenState(int, enum.Enum):
    VAILD = 1
    SUSPENDED = 3
    REVOKED = 5


class ApiToken(DefaultBase):
    __tablename__ = 'api_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String)
    state = Column(Integer)
    created = Column(Integer)  # Unix timestamp
    till = Column(Integer)  # Unix timestamp
    description = Column(String)

    @property
    def expired(self):
        return self.till != 0 and self.till < time.time()
