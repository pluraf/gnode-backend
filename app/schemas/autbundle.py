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


from pydantic import BaseModel
from typing import Optional


class AuthbundleListResponse(BaseModel):
    authbundle_id: str
    service_type: str
    auth_type: str
    description: Optional[str] = ""

class AuthbundleDetailsResponse(BaseModel):
    authbundle_id: str
    service_type: str
    auth_type: str
    description: Optional[str] = ""
    username: Optional[str] = None
