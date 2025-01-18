import requests
import yaml

# BASE_URL = "https://gitlab.com/ai-validation/regelspraak/-/raw/master/rules"
BASE_URL = "/Users/anneschuth/poc-machine-law/law"


def get_rule_spec(rule_uuid="4d8c7237-b930-4f0f-aaa3-624ba035e449"):
    if BASE_URL.startswith("http://"):
        # try:
        rule_url = f"{BASE_URL}/zorgtoeslagwet/{rule_uuid}.yaml"
        print(f"Getting spec from: {rule_url}")
        response = requests.get(rule_url)
        response.raise_for_status()
        return yaml.safe_load(response.text)
        # except requests.exceptions.RequestException as e:
        #     #raise HTTPException(status_code=404, detail=f"Rule with UUID {rule_uuid} not found")
        #     raise Error(status_code=404, detail=f"Rule with UUID {rule_uuid} not found")
    else:
        with open(f"{BASE_URL}/zorgtoeslagwet/{rule_uuid}.yaml") as f:
            return yaml.safe_load(f.read())
