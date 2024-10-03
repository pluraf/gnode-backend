from fastapi import APIRouter

from typing import Dict

router = APIRouter()

def read_version_from_file(file_path: str) -> Dict[str, str]:
    api_versions = {}

    with open(file_path, "r") as file:
        for line in file:
            api_name, version = line.split("=")
            api_name = api_name.strip().replace("API_VERSION", "").strip()
            version = version.strip()
            api_versions[api_name] = version 
    return api_versions


@router.get("/")
async def api_version_get():
    api_versions = read_version_from_file("./api_versions.txt")
    return api_versions