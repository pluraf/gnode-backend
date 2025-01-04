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


from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str
    is_admin: bool


class UserCreate(UserBase):
    password: str


# For security reasons, password not added to User
class User(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes = True)


class UserAuth(User):
    hashed_password: str
