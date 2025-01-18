from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Path, Header, Query
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.status import Status, StatusCode
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse

from engine import RulesEngine
from explanations.alef_html_explanation import YamlToAlefHtml
from services.services import ServiceProvider
from utils import parse_traceparent, create_traceparent, get_rule_spec

# Initialize OpenTelemetry
resource = Resource.create({"service.name": "toeslagen-regels2-service"})
tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://toeslagen-ldv-collector:4317")  # Adjust endpoint as needed
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

# Get tracer
tracer = trace.get_tracer(__name__)


class FinancialPicture(BaseModel):
    income: int
    netWorth: int


class CareBenefitData(BaseModel):
    financialPicture: FinancialPicture
    partner: Optional[FinancialPicture] = None


class CareBenefit(BaseModel):
    amount: Optional[int] = None
    reason: Optional[str] = None
    data: Optional[CareBenefitData] = None


# Error reasons
INCOME_ABOVE_THRESHOLD = "income_above_threshold"
NETWORTH_ABOVE_THRESHOLD = "networth_above_threshold"
HEALTH_INSURANCE_INVALID = "health_insurance_invalid"
DATE_OF_BIRTH_UNKNOWN = "date_of_birth_unknown"
PERSON_AGE_BELOW_THRESHOLD = "person_age_below_threshold"

# Initialize the services
provider = ServiceProvider("services.yaml")


async def calculate(bsn, datetime_param, rule_uuid, traceparent):
    spec = get_rule_spec(rule_uuid) if rule_uuid else get_rule_spec()
    engine = RulesEngine(spec=spec, service_provider=provider)
    with tracer.start_span("rules_engine.evaluate") as span:

        trace_id, parent_id = parse_traceparent(traceparent)
        if trace_id and parent_id:
            span.set_attributes({
                "dpl.rva.foreign.trace_id": trace_id,
                "dpl.rva.foreign.operation_id": parent_id
            })

        span.set_attributes({
            "dpl.algoritmes.type": "regels2",
            "dpl.core.user": bsn,
            "dpl.rva.activity.id": "5879ea7b-cc83-4ff6-8ed1-1545b5623ef8",
            "dpl.algoritmes.id": spec.get("uuid"),
            "dpl.algoritmes.brp.burgerservicenummer": bsn
        })
        try:
            span.set_attribute("bsn", bsn)

            service_context = {'bsn': bsn,
                               'traceparent': create_traceparent(str(span.get_span_context().trace_id),
                                                                 str(span.get_span_context().span_id))}
            if datetime_param:
                service_context['datetime'] = datetime_param
                span.set_attribute("dpl.algoritmes.datetime", datetime_param.isoformat())

            response = await run_in_threadpool(
                engine.evaluate,
                service_context=service_context
            )

            result = response['results']
            values = response['values']
            print(result)

            span.set_attributes({f"dpl.algoritmes.params.{k[1:]}": v for k, v in values.items() if v})

            # Convert income from float to int (cents), default to 0 if not present
            personal_income = int(values.get('$NATUURLIJKE_PERSOON.toetsingsinkomen', 0))

            # Get net worth data with safe defaults
            personal_net_worth = int(values.get('$NATUURLIJKE_PERSOON.vermogen', 0))
            combined_net_worth = int(values.get('$NATUURLIJKE_PERSOON.gezamenlijk_vermogen', 0))

            # Create financial picture for the person
            financial_picture = FinancialPicture(
                income=personal_income,
                netWorth=personal_net_worth
            )

            # Create partner financial picture if there is a partner
            partner_financial_picture = None
            if values.get('$NATUURLIJKE_PERSOON.heeft_toeslagpartner', False):
                partner_income = int(values.get('$NATUURLIJKE_PERSOON.partner.toetsingsinkomen', 0))
                # For partner's net worth, we use the difference between combined and personal
                partner_net_worth = combined_net_worth - personal_net_worth
                partner_financial_picture = FinancialPicture(
                    income=partner_income,
                    netWorth=partner_net_worth
                )

            # Create care benefit data
            care_benefit_data = CareBenefitData(
                financialPicture=financial_picture,
                partner=partner_financial_picture
            )

            amount = int(result.get("HOOGTE_TOESLAG", 0) / 12) if result.get("VERZEKERDE_ZORGTOESLAG", False) else 0
            amount = max(0, amount)
            reason = None
            if not amount:
                if not values.get('$NATUURLIJKE_PERSOON.verzekerde_zvw', False):
                    reason = HEALTH_INSURANCE_INVALID
                elif values.get('$NATUURLIJKE_PERSOON.leeftijd') is None:
                    reason = DATE_OF_BIRTH_UNKNOWN
                elif values.get('$NATUURLIJKE_PERSOON.leeftijd', 0) < 18:
                    reason = PERSON_AGE_BELOW_THRESHOLD
                elif combined_net_worth > 120000:  # Example threshold, adjust as needed
                    reason = NETWORTH_ABOVE_THRESHOLD
                else:
                    reason = INCOME_ABOVE_THRESHOLD

            span.set_attributes({
                "dpl.algoritmes.toeslagen.amount": amount
            })

            care_benefit = CareBenefit(
                amount=amount,
                reason=reason,
                data=care_benefit_data
            )

            print(values)
            print(care_benefit)
            span.set_status(Status(StatusCode.OK))
            return care_benefit

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR), str(e))
            raise


app = FastAPI(title="Toeslagen Regels", version="0.1")


@app.get("/v0/rule/benefits/care", response_class=HTMLResponse)
async def get_rule(rule_uuid: Optional[str] = None):
    spec = get_rule_spec(rule_uuid) if rule_uuid else get_rule_spec()
    converter = YamlToAlefHtml(spec)
    return converter.convert()


@app.get("/v0/benefits/care/{bsn}", response_model=CareBenefit)
async def calculate_care_benefit(bsn: str = Path(..., pattern="^[0-9]{9}$"),
                                 rule_uuid: Optional[str] = None,
                                 datetime_param: Optional[datetime] = Query(None, alias="datetime"),
                                 traceparent: Optional[str] = Header(None)
                                 ):
    return await calculate(bsn, datetime_param, rule_uuid, traceparent)


@app.post("/v0/test/benefits/care/{bsn}", response_model=CareBenefit)
async def calculate_care_benefit_post(bsn: str = Path(..., pattern="^[0-9]{9}$"),
                                      rule_uuid: Optional[str] = None,
                                      datetime_param: Optional[datetime] = Query(None, alias="datetime"),
                                      traceparent: Optional[str] = Header(None)
                                      ):
    return await calculate(bsn, datetime_param, rule_uuid, traceparent)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
