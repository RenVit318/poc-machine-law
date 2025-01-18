import asyncio

from behave import given, when, then

from engine import RulesEngine
from services.services import ServiceProvider
from utils import RuleResolver


@given('het is het jaar "{year}"')
def step_impl(context, year):
    reference_date = f"{year}-01-01"
    resolver = RuleResolver()
    spec = resolver.get_rule_spec("zorgtoeslagwet", reference_date)
    context.provider = ServiceProvider("services.yaml")
    context.engine = RulesEngine(spec=spec, service_provider=context.provider)
    context.service_context['reference_date'] = reference_date


@given('een persoon met BSN "{bsn}"')
def step_impl(context, bsn):
    context.service_context['bsn'] = bsn


@given('de persoon is "{age}" jaar oud')
def step_impl(context, age):
    context.test_data["@BRP.age"] = int(age)


@given('de persoon heeft een zorgverzekering')
def step_impl(context):
    context.test_data["@RVZ.has_insurance"] = True


@given('de persoon heeft geen toeslagpartner')
def step_impl(context):
    context.test_data["@BRP.has_partner"] = False


@given('de persoon heeft een inkomen van "{income}" euro')
def step_impl(context, income):
    context.test_data["@UWV.income"] = int(float(income) * 100)


@given('de persoon heeft studiefinanciering van "{amount}" euro')
def step_impl(context, amount):
    context.test_data["@DUO.study_grant"] = int(float(amount) * 100)


@given('de persoon heeft een vermogen van "{worth}" euro')
def step_impl(context, worth):
    context.test_data["@BELASTINGDIENST.net_worth"] = int(float(worth) * 100)


@when('de zorgtoeslag wordt berekend')
def step_impl(context):
    context.result = asyncio.run(
        context.engine.evaluate(
            service_context=context.service_context,
            overwrite_input=context.test_data
        )
    )


@then('heeft de persoon recht op zorgtoeslag')
def step_impl(context):
    assert context.result['output']['is_verzekerde_zorgtoeslag']['value'] == True


@then('heeft de persoon geen recht op zorgtoeslag')
def step_impl(context):
    assert not context.result['output']['is_verzekerde_zorgtoeslag']['value']


@then('is voldaan aan de voorwaarden')
def step_impl(context):
    assert context.result['requirements_met'] == True


@then('is niet voldaan aan de voorwaarden')
def step_impl(context):
    assert context.result['requirements_met'] == False


@then('is het toeslagbedrag hoger dan "{amount}" euro')
def step_impl(context, amount):
    toeslag_cents = context.result['output']['hoogte_toeslag']['value']
    assert toeslag_cents > int(float(amount) * 100)


@then('is het toeslagbedrag "{amount}" euro')
def step_impl(context, amount):
    assert context.result['output']['hoogte_toeslag']['value'] == int(float(amount) * 100)
