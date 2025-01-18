import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import yaml

# BASE_URL = "https://gitlab.com/ai-validation/regelspraak/-/raw/master/rules"
BASE_URL = "/Users/anneschuth/poc-machine-law/law/zorgtoeslagwet"


@dataclass
class RuleSpec:
    path: str
    uuid: str
    name: str
    law: str
    valid_from: datetime
    service: str

    @classmethod
    def from_yaml(cls, path: str) -> 'RuleSpec':
        """Create RuleSpec from a YAML file path"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        return cls(
            path=path,
            uuid=data.get('uuid', ''),
            name=data.get('name', ''),
            law=data.get('law', ''),
            valid_from=data.get('valid_from') if isinstance(data.get('valid_from'), datetime) else datetime.combine(
                data.get('valid_from'), datetime.min.time()),
            service=data.get('service', '')
        )


class RuleResolver:
    def __init__(self):
        self.rules_dir = BASE_URL
        self.rules: List[RuleSpec] = []
        self._load_rules()

    def _load_rules(self):
        """Load all rule specifications from the rules directory"""
        for root, _, files in os.walk(self.rules_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    path = os.path.join(root, file)
                    try:
                        rule = RuleSpec.from_yaml(path)
                        self.rules.append(rule)
                    except Exception as e:
                        print(f"Error loading rule from {path}: {e}")
        self.laws_by_service = defaultdict(set)
        for rule in self.rules:
            self.laws_by_service[rule.service].add(rule.law)

    def get_service_laws(self):
        return self.laws_by_service

    def find_rule(self, law: str, reference_date: str) -> Optional[RuleSpec]:
        """Find the applicable rule for a given law and reference date"""
        ref_date = datetime.strptime(reference_date, '%Y-%m-%d')

        # Filter rules for the given law
        law_rules = [r for r in self.rules if r.law == law]

        if not law_rules:
            raise ValueError(f"No rules found for law: {law}")

        # Find the most recent valid rule before the reference date
        valid_rules = [r for r in law_rules if r.valid_from <= ref_date]

        if not valid_rules:
            raise ValueError(f"No valid rules found for law {law} at date {reference_date}")

        # Return the most recently valid rule
        return max(valid_rules, key=lambda r: r.valid_from)

    def get_rule_spec(self, law: str, reference_date: str) -> dict:
        """Get the rule specification as a dictionary"""
        rule = self.find_rule(law, reference_date)
        if not rule:
            raise ValueError(f"No rule found for {law} at {reference_date}")

        with open(rule.path, 'r') as f:
            return yaml.safe_load(f)


if __name__ == "__main__":
    reference_date = "2025-01-01"
    resolver = RuleResolver()
    spec = resolver.get_rule_spec("zorgtoeslagwet", reference_date)
    assert spec['uuid'] == '4d8c7237-b930-4f0f-aaa3-624ba035e449'
