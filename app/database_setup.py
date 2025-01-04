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


import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

GNODE_DATABASE_URL = "sqlite:///" + os.getenv("GNODE_DB_DIR") + "/gnode.sqlite"
AUTHBUNDLE_DATABASE_URL = "sqlite:///" + os.getenv("GNODE_DB_DIR") + "/authbundles.sqlite"

default_engine = create_engine(GNODE_DATABASE_URL, connect_args={"check_same_thread": False})
auth_engine = create_engine(AUTHBUNDLE_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=default_engine)

DefaultBase = declarative_base()
AuthBase = declarative_base()
