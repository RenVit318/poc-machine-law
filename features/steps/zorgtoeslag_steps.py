import asyncio
from typing import Any

from behave import given
from behave import when, then


def parse_value(value: str) -> Any:
    """Parse string value to appropriate type"""
    # Try to convert to int (for monetary values in cents)
    try:
        return int(value)
    except ValueError:
        pass

    # Try to parse date
    if '-' in value and len(value) == 10:
        try:
            from datetime import datetime
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Return as string for other cases
    return value


@given('de volgende brongegevens')
def step_impl(context):
    """
    Process source data table and set up overwrites in the Services instance
    Table format:
    | Service | Law | Table | Field | Value |
    """
    # Ensure we have a table
    if not context.table:
        raise ValueError("No table provided for source data")

    # Process each row
    for row in context.table:
        service = row['Service'].strip()
        table = row['Table'].strip()
        field = row['Field'].strip()
        value = parse_value(row['Value'].strip())

        # Set the override in our services instance
        context.services.set_source_value(
            service=service,
            table=table,
            field=field,
            value=value
        )


@given('het is het jaar "{year}"')
def step_impl(context, year):
    context.reference_date = f"{year}-01-01"


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


@when('de {law} wordt uitgevoerd door {service}')
def step_impl(context, law, service):
    context.result = asyncio.run(
        context.services.evaluate(
            service,
            law=law,
            reference_date=context.reference_date,
            service_context=context.service_context,
            overwrite_input=context.test_data
        )
    )


@then('heeft de persoon recht op zorgtoeslag')
def step_impl(context):
    assert context.result.output['is_verzekerde_zorgtoeslag'] == True


@then('heeft de persoon geen recht op zorgtoeslag')
def step_impl(context):
    assert not context.result.output['is_verzekerde_zorgtoeslag']


@then('is voldaan aan de voorwaarden')
def step_impl(context):
    assert context.result.requirements_met == True


@then('is niet voldaan aan de voorwaarden')
def step_impl(context):
    assert context.result.requirements_met == False


@then('is het toeslagbedrag hoger dan "{amount}" euro')
def step_impl(context, amount):
    assert context.result.output['hoogte_toeslag'] > int(float(amount) * 100)


@then('is het toeslagbedrag "{amount}" euro')
def step_impl(context, amount):
    assert context.result.output['hoogte_toeslag'] == int(float(amount) * 100)
