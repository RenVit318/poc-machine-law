import asyncio
from pprint import pprint

from engine import RulesEngine
from services.services import ServiceProvider
from utils import get_rule_spec


async def run(service_context, engine, data=None):
    result = await engine.evaluate(service_context=service_context, overwrite_input=data)
    path = result.pop('path')
    pprint(path)
    pprint(result)

async def main():
    spec = get_rule_spec()

    provider = ServiceProvider("services.yaml")
    engine = RulesEngine(spec=spec, service_provider=provider)

    service_context = {'bsn': '999993653'}

    # await run(service_context, engine)

    data = {"@BRP.age": 17}
    await run(service_context, engine, data)


if __name__ == "__main__":
    asyncio.run(main())
