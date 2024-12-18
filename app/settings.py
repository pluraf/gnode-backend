ALGORITHM = "ES256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

TOKEN_AUTH_URL = "/api/auth/token"

ZMQ_MQBC_SOCKET = "ipc:///tmp/mqbc-zmq.sock"
ZMQ_M2EB_SOCKET = "ipc:///tmp/m2eb-zmq.sock"
ZMQ_GCLIENT_SOCKET = "ipc:///run/gnode/gclient.sock"

MQBC_SERVICE_NAME = "mqbc.service"
M2EB_SERVICE_NAME = "m2eb.service"
GCLOUD_SERVICE_NAME = "gnode-cloud-client.service"
