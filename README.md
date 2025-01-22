# Proof of Concept Machine Law


## Law
https://github.com/MinBZK/poc-machine-law/tree/main/law

## Machine
https://github.com/MinBZK/poc-machine-law/blob/main/engine.py

## Running the Machine

```shell
git clone git@github.com:MinBZK/poc-machine-law.git
cd poc-machine-law
uv sync
uv run behave features/zorgtoeslag.feature:38 --no-capture -v --define log_level=DEBUG
```
