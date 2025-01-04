# SPDX-License-Identifier: Apache-2.0

# Copyright (c) 2024 Pluraf Embedded AB <code@pluraf.com>

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


from app.database_setup import AuthBase
from sqlalchemy import Column, String, LargeBinary


class Authbundle(AuthBase):
    __tablename__ = 'authbundles'
    authbundle_id = Column(String, primary_key=True)
    service_type = Column(String)
    auth_type = Column(String)
    username = Column(String)
    password = Column(String)
    keyname = Column(String)
    keydata = Column(LargeBinary)
    description = Column(String)
