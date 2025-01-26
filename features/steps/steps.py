import asyncio
from typing import Any
from unittest import TestCase

import pandas as pd
from behave import given
from behave import when, then

from service import Services

assertions = TestCase()


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


@given('de volgende {service} {table} gegevens')
def step_impl(context, service, table):
    if not context.table:
        raise ValueError(f"No table provided for {table}")

    # Convert table to DataFrame
    data = []
    for row in context.table:
        processed_row = {k: v if k in {'bsn', 'partner_bsn', 'jaar'} else parse_value(v) for k, v in row.items()}
        data.append(processed_row)

    df = pd.DataFrame(data)

    # Set the DataFrame in services
    context.services.set_source_dataframe(service, table, df)


@given('de datum is "{date}"')
def step_impl(context, date):
    context.root_reference_date = date
    context.services = Services(date)


@given('een persoon met BSN "{bsn}"')
def step_impl(context, bsn):
    context.parameters['BSN'] = bsn


@when('de {law} wordt uitgevoerd door {service}')
def step_impl(context, law, service):
    context.result = asyncio.run(
        context.services.evaluate(
            service,
            law=law,
            reference_date=context.root_reference_date,
            parameters=context.parameters,
            overwrite_input=context.test_data
        )
    )


@then('heeft de persoon recht op zorgtoeslag')
def step_impl(context):
    assertions.assertTrue(
        context.result.output['is_verzekerde_zorgtoeslag'],
        "Expected person to be eligible for healthcare allowance, but they were not"
    )


@then('heeft de persoon geen recht op zorgtoeslag')
def step_impl(context):
    assertions.assertFalse(
        context.result.output['is_verzekerde_zorgtoeslag'],
        "Expected person to not be eligible for healthcare allowance, but they were"
    )


@then('is voldaan aan de voorwaarden')
def step_impl(context):
    assertions.assertTrue(
        context.result.requirements_met,
        "Expected requirements to be met, but they were not"
    )


@then('is niet voldaan aan de voorwaarden')
def step_impl(context):
    assertions.assertFalse(
        context.result.requirements_met,
        "Expected requirements to not be met, but they were"
    )


@then('is het toeslagbedrag hoger dan "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['hoogte_toeslag']
    expected_min = int(float(amount) * 100)
    assertions.assertGreater(
        actual_amount,
        expected_min,
        f"Expected allowance amount to be greater than {amount} euros, but was {actual_amount / 100:.2f} euros"
    )


def compare_euro_amount(actual_amount, amount):
    expected_amount = int(float(amount) * 100)
    assertions.assertEqual(
        actual_amount,
        expected_amount,
        f"Expected amount to be {amount} euros, but was {actual_amount / 100:.2f} euros"
    )


@then('is het toeslagbedrag "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['hoogte_toeslag']
    compare_euro_amount(actual_amount, amount)


@then('is het pensioen "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output['pension_amount']
    compare_euro_amount(actual_amount, amount)
