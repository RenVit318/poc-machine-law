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

## Todo
In no particular order

- implement passing on reference dates to sources (understand what `january_first` means)
- add a second set of laws (next to zorgtoeslagwet)
- how do general laws (right to appeal for instance) impact this? should we mark what can and cannot be appealed?
- tooling to transform laws into machine law
- detecting deadlocks/livelocks/loops
- explaining runs of machine laws to a citizen
