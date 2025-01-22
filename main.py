import asyncio
from pprint import pprint

from engine import RulesEngine
from service import Services
from utils import RuleResolver


async def run(service_context, engine, data=None):
    result = await engine.evaluate(service_context=service_context, overwrite_input=data)
    path = result.pop('path')
    pprint(path)
    pprint(result)


async def main():
    reference_date = "2025-01-01"
    resolver = RuleResolver()
    spec = resolver.get_rule_spec("zorgtoeslagwet", reference_date)

    provider = Services()
    engine = RulesEngine(spec=spec, service_provider=provider)

    service_context = {'bsn': '999993653'}

    await run(service_context, engine)

    data = {"@RvIG.age": 19}
    await run(service_context, engine, data)


if __name__ == "__main__":
    asyncio.run(main())
