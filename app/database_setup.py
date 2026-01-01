# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2024-2025 Pluraf Embedded AB <code@pluraf.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

GNODE_DATABASE_URL = "sqlite:///" + os.getenv("GNODE_DB_DIR") + "/gnode.sqlite"
AUTHBUNDLE_DATABASE_URL = "sqlite:///" + os.getenv("GNODE_DB_DIR") + "/authbundles.sqlite"

default_engine = create_engine(GNODE_DATABASE_URL, connect_args={"check_same_thread": False})
auth_engine = create_engine(AUTHBUNDLE_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocalDefault = sessionmaker(autocommit=False, autoflush=False, bind=default_engine)

DefaultBase = declarative_base()
AuthBase = declarative_base()
