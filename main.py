import asyncio
from pprint import pprint

from services.services import ServiceProvider
from engine import RulesEngine
from utils import get_rule_spec


async def main():
    spec = get_rule_spec()

    provider = ServiceProvider("services.yaml")
    engine = RulesEngine(spec=spec, service_provider=provider)

    service_context = {'bsn': '999993653'}

    # result = await engine.evaluate(service_context=service_context)
    # pprint(result)

    data = {"@BRP.age": 19}
    result = await engine.evaluate(service_context=service_context, overwrite_input=data)
    path = result.pop('path')
    pprint(result)


if __name__ == "__main__":
    asyncio.run(main())
