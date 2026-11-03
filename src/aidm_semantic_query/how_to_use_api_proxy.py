""" This file was taken originally from AIDM course moodle
This file shouln't be modified
"""

import hashlib
import json
import logging
import os
import pathlib
from concurrent.futures import ThreadPoolExecutor

import requests

logger = logging.getLogger(__name__)

URL = "http://runner-aidm.dm.informatik.tu-darmstadt.de:8080"
CACHE_PATH = pathlib.Path(os.path.dirname(__file__)).joinpath("openai_cache").resolve()
MAX_WORKERS = 20  # mirrors restriction in proxy

CHAT_COMPLETIONS_MODELS = {
    "gpt-6.1-sol": {
        "usd_per_1m_input_tokens": 2.0,
        "usd_per_1m_output_tokens": 10.0,
        "usd_per_1m_cached_input_tokens": 0.1,
        "usd_per_1m_cache_write_input_tokens": 2.5
    },
    "gpt-6.1-terra": {
        "usd_per_1m_input_tokens": 1.0,
        "usd_per_1m_output_tokens": 5.0,
        "usd_per_1m_cached_input_tokens": 0.05,
        "usd_per_1m_cache_write_input_tokens": 1.25
    },
    "gpt-6-luna": {
        "usd_per_1m_input_tokens": 0.1,
        "usd_per_1m_output_tokens": 0.5,
        "usd_per_1m_cached_input_tokens": 0.01,
        "usd_per_1m_cache_write_input_tokens": 0.125
    }
}

EMBEDDING_MODELS = {
    "text-embedding-3-small": {"usd_per_1m_input_tokens": 0.02},
    "text-embedding-3-large": {"usd_per_1m_input_tokens": 0.13}
}


def cost_for_chat_completion(response: dict) -> float:
    """Compute the USD cost for one chat completion response."""
    usage = response["usage"]
    model_info = CHAT_COMPLETIONS_MODELS[response["model"]]

    input_tokens = usage["prompt_tokens"]
    details = usage.get("prompt_tokens_details") or {}
    cached_input_tokens = details.get("cached_tokens") or 0
    input_tokens -= cached_input_tokens
    cache_write_input_tokens = details.get("cache_write_tokens") or 0
    input_tokens -= cache_write_input_tokens

    output_tokens = usage["completion_tokens"]

    input_cost = (
            input_tokens * model_info["usd_per_1m_input_tokens"] / 1_000_000
            + cached_input_tokens * model_info["usd_per_1m_cached_input_tokens"] / 1_000_000
            + cache_write_input_tokens * model_info["usd_per_1m_cache_write_input_tokens"] / 1_000_000
    )

    output_cost = output_tokens * model_info["usd_per_1m_output_tokens"] / 1_000_000

    if usage["prompt_tokens"] <= 272_000:
        total_cost = input_cost + output_cost
    else:
        total_cost = 2 * input_cost + 1.5 * output_cost

    return total_cost


def cost_for_embedding(response: dict) -> float:
    """Compute the USD cost for one embedding response."""
    usage = response["usage"]
    model_info = EMBEDDING_MODELS[response["model"]]
    return usage["prompt_tokens"] * model_info["usd_per_1m_input_tokens"] / 1_000_000


def log_monthly_budget() -> None:
    """Log the remaining monthly budget percentage."""

    if "AIDM_USER" not in os.environ.keys():
        logger.error("Set AIDM_USER environment variable with your secret user name from Moodle!")
        exit()

    http_response = requests.post(
        url=URL + "/budget",
        json={"user": os.environ["AIDM_USER"]},
        headers={"Content-Type": "application/json"}
    )

    if http_response.status_code != 200:
        logger.error(f"request failed: {http_response} {http_response.content}")
        http_response.raise_for_status()

    logger.info(f"remaining monthly cost budget: {int(http_response.json()['budget'] * 100)}%")


def execute_and_cache_request(request: dict, url: str) -> dict:
    """Execute and cache one API request."""
    if "AIDM_USER" not in os.environ.keys():
        logger.error("Set AIDM_USER environment variable with your secret user name from Moodle!")
        exit()

    request["user"] = os.environ["AIDM_USER"]

    CACHE_PATH.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_PATH / f"{hashlib.sha256(bytes(json.dumps(request), 'utf-8')).hexdigest()}.json"

    if cache_path.is_file():
        with open(cache_path, "r", encoding="utf-8") as file:
            cached_pair = json.load(file)
        if request == cached_pair["request"]:
            return cached_pair["response"]

    http_response = requests.post(url=url, json=request, headers={"Content-Type": "application/json"})

    if http_response.status_code != 200:
        logger.error(f"request failed: {http_response} {http_response.content}")
        http_response.raise_for_status()

    response = http_response.json()

    if http_response.status_code == 200:
        with open(cache_path, "w", encoding="utf-8") as cache_file:
            json.dump({"request": request, "response": response}, cache_file)

    return response


def execute_chat_completions_request(request: dict) -> dict:
    """Execute one chat completions request."""
    return execute_and_cache_request(request, URL + "/chat_completions")


def execute_embeddings_request(request: dict) -> dict:
    """Execute one embeddings request."""
    return execute_and_cache_request(request, URL + "/embeddings")


if __name__ == '__main__':
    logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", level=logging.INFO)

    # Log monthly budget percentage
    log_monthly_budget()

    # Execute some chat completion requests
    cc_requests = []
    for ix in range(10):
        req = {
            "model": "gpt-6-luna",
            "messages": [
                {
                    "role": "user",
                    "content": f"Return a comma-separated list of the first {ix + 1} prime numbers."
                }
            ]
        }
        cc_requests.append(req)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for response in executor.map(execute_chat_completions_request, cc_requests):
            cost = cost_for_chat_completion(response)
            logger.info(f"Response: {response['choices'][0]['message']['content']} Cost: {cost}")

    # Execute some embedding requests
    emb_requests = []
    for ix in range(10):
        req = {
            "model": "text-embedding-3-small",
            "input": [
                f"This is sentence number {ix * 2}.",
                f"This is sentence number {ix * 2 + 1}."
            ]
        }
        emb_requests.append(req)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for response in executor.map(execute_embeddings_request, emb_requests):
            cost = cost_for_embedding(response)
            logger.info(
                f"Embeddings: {response['data'][0]['embedding'][:5]}, {response['data'][1]['embedding'][:5]} Cost: {cost}"
            )

    # Log remaining monthly budget percentage
    log_monthly_budget()
