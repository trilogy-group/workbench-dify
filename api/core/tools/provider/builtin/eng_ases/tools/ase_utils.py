import requests
import logging
import time
import os

def trigger_ase(procedure: str, inputs: dict):
    API_KEY = os.environ.get("ENG_ASE_API_KEY")
    CALLBACK_SERVICE_API_KEY = os.environ.get("CALLBACK_SERVICE_API_KEY")

    ase_url = "https://wbkktudmnocpkxe35tx62majaa0tnokz.lambda-url.us-east-1.on.aws/"
    ase_request_headers = {"X-Api-Key": API_KEY}
    callback_service_endpoint = "https://48j93p3119.execute-api.us-east-1.amazonaws.com/api"
    callback_request_headers = {"Authorization": f"Basic {CALLBACK_SERVICE_API_KEY}"}

    # Generate conversation ID 
    response = requests.post(url=f"{callback_service_endpoint}/callback", headers=callback_request_headers)
    response.raise_for_status()
    callback_id = response.json()['id']
    logging.info(f"Generate callback ID is: {callback_id}")

    # Invoke the ASE
    data = {
        "procedure": procedure,
        "inputs": inputs,
        "async": True,
        "callbackUrl": f"{callback_service_endpoint}/callback/{callback_id}"
    }
    logging.info(f"Triggering ASE with data: {data}")
    response = requests.post(ase_url, headers=ase_request_headers, json=data)
    response.raise_for_status()
    logging.info(f"Received response from ASE: {response}")

    # Poll the callback service for ASE response
    pending_retries = 100
    while pending_retries > 0:
        response = requests.get(url=f"{callback_service_endpoint}/callback/{callback_id}", headers=callback_request_headers)
        response.raise_for_status()
        response_dict = response.json()
        if response_dict['status'] == 'COMPLETED':
            return response_dict['output']
        time.sleep(30)
        pending_retries -= 1

    return {"error": f"ASE timed out"}