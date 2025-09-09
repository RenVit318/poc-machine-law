import json
from typing import Any
from unittest import TestCase

import pandas as pd
from behave import given, when, then

from machine.service import Services

assertions = TestCase()


def parse_value(value: str) -> Any:
    """Parse string value to appropriate type"""
    # Try to parse as JSON
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    # Try to convert to int (for monetary values in cents)
    try:
        return int(value)
    except ValueError:
        pass

    return value


@given("de volgende {service} {table} gegevens")
def step_impl(context, service, table):
    if not context.table:
        raise ValueError(f"No table provided for {table}")

    # Convert table to DataFrame
    data = []
    for row in context.table:
        processed_row = {
            k: v if k in {"bsn", "partner_bsn", "jaar", "kind_bsn"} else parse_value(v)
            for k, v in row.items()
        }
        data.append(processed_row)

    df = pd.DataFrame(data)

    # Set the DataFrame in services
    context.services.set_source_dataframe(service, table, df)

# Claude made these step definitions to read data from tables - can we not just use the function above for generic data import?
@given('een aanvraag met ID "{aanvraag_id}"')
def step_impl(context, aanvraag_id):
    """Set the request ID for AVG data sharing scenarios"""
    if not hasattr(context, "parameters"):
        context.parameters = {}
    context.parameters["AANVRAAG_ID"] = aanvraag_id


# AVG-specific step definitions
@given("de volgende rechtsgrondslag gegevens")
def step_rechtsgrondslag_gegevens(context):
    """Handle legal basis data for AVG scenarios"""
    if not context.table:
        raise ValueError("No table provided for rechtsgrondslag gegevens")
    
    data = []
    for row in context.table:
        processed_row = {k: parse_value(v) for k, v in row.items()}
        data.append(processed_row)
    
    df = pd.DataFrame(data)
    context.services.set_source_dataframe("VERWERKINGSVERANTWOORDELIJKE", "rechtsgrondslag_claims", df)


@given("de volgende data categorieën")
def step_data_categorieen(context):
    """Handle data categories for AVG scenarios"""
    if not context.table:
        raise ValueError("No table provided for data categorieën")
    
    data = []
    for row in context.table:
        processed_row = {k: parse_value(v) for k, v in row.items()}
        data.append(processed_row)
    
    df = pd.DataFrame(data)
    context.services.set_source_dataframe("VERWERKINGSVERANTWOORDELIJKE", "data_sharing_requests", df)


@given("de volgende beveiligingsmaatregelen")
def step_beveiligingsmaatregelen(context):
    """Handle security measures for AVG scenarios"""
    if not context.table:
        raise ValueError("No table provided for beveiligingsmaatregelen")
    
    data = []
    for row in context.table:
        processed_row = {k: parse_value(v) for k, v in row.items()}
        data.append(processed_row)
    
    df = pd.DataFrame(data)
    context.services.set_source_dataframe("VERWERKINGSVERANTWOORDELIJKE", "security_measures", df)


@then('bevat de uitkomst "{field_name}"')
def step_bevat_uitkomst(context, field_name):
    """Check that output contains a specific field"""
    assert hasattr(context, 'result'), "No result found in context"
    assert field_name in context.result, f"Field '{field_name}' not found in result: {context.result.keys()}"


@then('is de waarde van "{field_name}" gelijk aan "{expected_value}"')
def step_waarde_gelijk_aan(context, field_name, expected_value):
    """Check that a field has a specific value"""
    assert hasattr(context, 'result'), "No result found in context"
    assert field_name in context.result, f"Field '{field_name}' not found in result"
    
    actual_value = str(context.result[field_name])
    assert actual_value == expected_value, f"Expected '{expected_value}', got '{actual_value}'"


# Generic field value assertions
@then('is het {field_name} "{expected_value}"')
def step_impl(context, field_name, expected_value):
    """Assert specific field value with type-aware comparison"""
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No evaluation result to check")
    
    if field_name not in context.result.output:
        available_fields = list(context.result.output.keys())
        raise ValueError(
            f"Field {field_name} not found in output. Available fields: {available_fields}"
        )
    
    actual_value = context.result.output[field_name]
    
    # Type-aware comparison
    if expected_value.lower() in ["true", "false"]:
        expected_bool = expected_value.lower() == "true"
        assertions.assertEqual(actual_value, expected_bool)
    elif expected_value.isdigit():
        expected_int = int(expected_value)
        assertions.assertEqual(actual_value, expected_int)
    else:
        assertions.assertEqual(actual_value, expected_value)


@given('de datum is "{date}"')
def step_impl(context, date):
    context.root_reference_date = date
    context.services = Services(date)


@given('een persoon met BSN "{bsn}"')
def step_impl(context, bsn):
    context.parameters["BSN"] = bsn


@given('de datum van de verkiezingen is "{date}"')
def step_impl(context, date):
    context.parameters["VERKIEZINGSDATUM"] = date


def evaluate_law(context, service, law, approved=True):
    context.result = context.services.evaluate(
        service,
        law=law,
        parameters=context.parameters,
        reference_date=context.root_reference_date,
        overwrite_input=context.test_data,
        approved=approved
    )

    context.service = service
    context.law = law


@when("de {law} wordt uitgevoerd door {service} met wijzigingen")
def step_impl(context, law, service):
    evaluate_law(context, service, law, approved=False)


@when("de {law} wordt uitgevoerd door {service} met")
def step_impl(context, law, service):
    if not hasattr(context, "test_data"):
        context.test_data = {}

    # Process the table to get the input data
    for row in context.table:
        key = row.headings[0]
        value = row[key]
        # Special handling for JSON-like values
        if value.startswith('[') or value.startswith('{'):
            import json
            try:
                value = json.loads(value.replace("'", '"'))
            except json.JSONDecodeError:
                pass
        context.test_data[key] = value

    evaluate_law(context, service, law)


@when("de {law} wordt uitgevoerd door {service}")
def step_impl(context, law, service):
    evaluate_law(context, service, law)


@then("heeft de persoon recht op zorgtoeslag")
def step_impl(context):
    assertions.assertTrue(
        context.result.output["is_verzekerde_zorgtoeslag"],
        "Expected person to be eligible for healthcare allowance, but they were not",
    )


@then("heeft de persoon geen recht op zorgtoeslag")
def step_impl(context):
    assertions.assertFalse(
        context.result.output["is_verzekerde_zorgtoeslag"],
        "Expected person to not be eligible for healthcare allowance, but they were",
    )


@then("is voldaan aan de voorwaarden")
def step_impl(context):
    assertions.assertTrue(
        context.result.requirements_met,
        "Expected requirements to be met, but they were not",
    )


@then("is niet voldaan aan de voorwaarden")
def step_impl(context):
    assertions.assertFalse(
        context.result.requirements_met,
        "Expected requirements to not be met, but they were",
    )


@then('is het toeslagbedrag hoger dan "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output["hoogte_toeslag"]
    expected_min = int(float(amount) * 100)
    assertions.assertGreater(
        actual_amount,
        expected_min,
        f"Expected allowance amount to be greater than {amount} euros, but was {actual_amount / 100:.2f} euros",
    )


def compare_euro_amount(actual_amount, amount):
    expected_amount = int(float(amount) * 100)
    assertions.assertEqual(
        actual_amount,
        expected_amount,
        f"Expected amount to be {amount} euros, but was {actual_amount / 100:.2f} euros",
    )


@then('is het toeslagbedrag "{amount}" euro')
def step_impl(context, amount):
    if "hoogte_toeslag" in context.result.output:
        actual_amount = context.result.output["hoogte_toeslag"]
    elif "jaarbedrag" in context.result.output:
        actual_amount = context.result.output["jaarbedrag"]
    else:
        raise ValueError("No toeslag amount found in output")
    compare_euro_amount(actual_amount, amount)


@then('is het pensioen "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output["pensioenbedrag"]
    compare_euro_amount(actual_amount, amount)


@given('een kandidaat met BSN "{bsn}"')
def step_impl(context, bsn):
    if not hasattr(context, "parameters"):
        context.parameters = {}
    context.parameters["BSN"] = bsn


@given('een partij met ID "{party_id}"')
def step_impl(context, party_id):
    if not hasattr(context, "parameters"):
        context.parameters = {}
    context.parameters["PARTY_ID"] = party_id


@then("is de kandidaatstelling geldig")
def step_impl(context):
    assertions.assertTrue(
        context.result.requirements_met,
        "Expected candidacy to be valid, but it was not",
    )


@then("is de kandidaatstelling niet geldig")
def step_impl(context):
    assertions.assertFalse(
        context.result.requirements_met,
        "Expected candidacy to be invalid, but it was valid",
    )


@then("heeft de persoon stemrecht")
def step_impl(context):
    assertions.assertTrue(
        context.result.requirements_met, "Expected the person to have voting rights"
    )


@then("heeft de persoon geen stemrecht")
def step_impl(context):
    assertions.assertFalse(
        context.result.requirements_met, "Expected the person not to have voting rights"
    )


@given("de volgende kandidaatgegevens")
def step_impl(context):
    if not context.table:
        raise ValueError("No table provided for kandidaatgegevens")

    # Convert table to DataFrame
    data = []
    for row in context.table:
        processed_row = {
            "kandidaat_bsn": row["kandidaat_bsn"],
            "positie": int(row["positie"]) if row["positie"] != "..." else None,
            "acceptatie": parse_value(row["acceptatie"]),
        }
        if processed_row["positie"] is not None:  # Skip the ... rows
            data.append(processed_row)

    df = pd.DataFrame(data)

    # Set in test_data for user_input
    if not hasattr(context, "test_data"):
        context.test_data = {}

    # We need only kandidaat_bsn and positie for CANDIDATE_LIST
    candidate_list_df = df[["kandidaat_bsn", "positie"]]
    context.test_data["CANDIDATE_LIST"] = candidate_list_df

    # Get the acceptatie for the main candidate
    context.test_data["CANDIDATE_ACCEPTANCE"] = df["acceptatie"].iloc[0]


@then('is het bijstandsuitkeringsbedrag "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output["uitkeringsbedrag"]
    compare_euro_amount(actual_amount, amount)


@then('is de woonkostentoeslag "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output["woonkostentoeslag"]
    compare_euro_amount(actual_amount, amount)


@then('is het startkapitaal "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output["startkapitaal"]
    compare_euro_amount(actual_amount, amount)


@given("alle aanvragen worden beoordeeld")
def step_impl(context):
    context.services.case_manager.SAMPLE_RATE = 1.0


@when("de persoon dit aanvraagt")
def step_impl(context):
    # Case indienen met de uitkomst van de vorige berekening
    case_id = context.services.case_manager.submit_case(
        bsn=context.parameters["BSN"],
        service_type=context.service,
        law=context.law,
        parameters=context.result.input,
        claimed_result=context.result.output,
        approved_claims_only=True
    )

    # Case ID opslaan voor volgende stappen
    context.case_id = case_id


@then("wordt de aanvraag toegevoegd aan handmatige beoordeling")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertIsNotNone(case, "Expected case to exist")
    assertions.assertEqual(case.status, "IN_REVIEW", "Expected case to be in review")


@then('is de status "{status}"')
def step_impl(context, status):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertIsNotNone(case, "Expected case to exist")
    assertions.assertEqual(
        case.status, status, f"Expected status to be {status}, but was {case.status}"
    )


@when('de beoordelaar de aanvraag afwijst met reden "{reason}"')
def step_impl(context, reason):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    case.decide(
        verified_result=context.result.output,
        reason=reason,
        verifier_id="BEOORDELAAR",
        approved=False,
    )
    context.services.case_manager.save(case)


@then("is de aanvraag afgewezen")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertIsNotNone(case, "Expected case to exist")
    assertions.assertEqual(case.status, "DECIDED", "Expected case to be decided")
    assertions.assertFalse(case.approved, "Expected case to be rejected")


@when('de burger bezwaar maakt met reden "{reason}"')
def step_impl(context, reason):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    case.object(reason=reason)
    context.services.case_manager.save(case)


@when('de beoordelaar het bezwaar {approve} met reden "{reason}"')
def step_impl(context, approve, reason):
    approve = approve.lower() == "toewijst"
    case = context.services.case_manager.get_case_by_id(context.case_id)
    case.decide(
        verified_result=context.result.output,
        reason=reason,
        verifier_id="BEOORDELAAR",
        approved=approve,
    )
    context.services.case_manager.save(case)


@then("is de aanvraag toegekend")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertEqual(case.status, "DECIDED", "Expected case to be decided")
    assertions.assertTrue(case.approved, "Expected case to be approved")


@then("kan de burger in bezwaar gaan")
def step_impl(context):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertTrue(case.can_object(), "Expected case to be objectable")


@then('kan de burger niet in bezwaar gaan met reden "{reason}"')
def step_impl(context, reason):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertFalse(case.can_object(), "Expected case not to be objectable")
    assertions.assertEqual(
        reason,
        case.objection_status.get("not_possible_reason"),
        "Expected reasons to match",
    )


@then("kan de burger in beroep gaan bij {competent_court}")
def step_impl(context, competent_court):
    case = context.services.case_manager.get_case_by_id(context.case_id)
    assertions.assertTrue(case.can_appeal(), "Expected to be able to appeal")
    assertions.assertEqual(
        competent_court,
        case.appeal_status.get("competent_court"),
        "Expected another competent court",
    )


@when("de burger {chance} indient")
def step_impl(context, chance):
    """Submit a claim for data change"""
    if not context.table:
        raise ValueError("No table provided for claims")

    if not hasattr(context, "claims"):
        context.claims = []

    for row in context.table:
        claim_id = context.services.claim_manager.submit_claim(
            service=row["service"],
            key=row["key"],
            new_value=parse_value(row["nieuwe_waarde"]),
            reason=row["reden"],
            claimant="BURGER",
            case_id=None,
            evidence_path=row.get("bewijs"),
            law=row["law"],
            bsn=context.parameters["BSN"]
        )
        context.claims.append(claim_id)


@then("heeft de persoon recht op huurtoeslag")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    assertions.assertTrue(
        context.result.requirements_met,
        "Persoon heeft toch geen recht op huurtoeslag",
    )


@then('is de huurtoeslag "{amount}" euro')
def step_impl(context, amount):
    actual_amount = context.result.output["subsidiebedrag"]
    compare_euro_amount(actual_amount, amount)


@then("ontbreken er verplichte gegevens")
def step_impl(context):
    assertions.assertTrue(context.result.missing_required,
                          "Er zouden gegevens moeten ontbreken.")


@then("ontbreken er geen verplichte gegevens")
def step_impl(context):
    assertions.assertFalse(context.result.missing_required,
                           "Er zouden geen gegevens moeten ontbreken.")


@then('is het {field} "{amount}" eurocent')
def step_impl(context, field, amount):
    actual_amount = context.result.output[field]
    expected_amount = int(amount)
    assertions.assertEqual(
        actual_amount,
        expected_amount,
        f"Expected {field} to be {amount} eurocent, but was {actual_amount} eurocent")


@then("heeft de persoon recht op kinderopvangtoeslag")
def step_impl(context):
    assertions.assertTrue(
        "is_gerechtigd" in context.result.output and context.result.output["is_gerechtigd"],
        "Expected person to be eligible for childcare allowance, but they were not",
    )

@then("heeft de persoon geen recht op kinderopvangtoeslag")
def step_impl(context):
    assertions.assertTrue(
        "is_gerechtigd" not in context.result.output or not context.result.output["is_gerechtigd"],
        "Expected person to NOT be eligible for childcare allowance, but they were",
    )


@then('controle vereist_{assessment_type} is niet leeg')
def step_impl(context, assessment_type):
    """Check that an assessment field is not null"""
    field_name = f"vereist_{assessment_type}"
    if field_name not in context.result.output:
        raise AssertionError(f"Field '{field_name}' not found in result: {context.result.output.keys()}")
    
    value = context.result.output[field_name]
    assertions.assertIsNotNone(value, f"Expected {field_name} to not be null, but it was null")
    if isinstance(value, str):
        assertions.assertNotEqual(value.lower(), "null", f"Expected {field_name} to not be 'null' string, but it was")


@then('controle vereist_{assessment_type} bevat "{text}"')
def step_impl(context, assessment_type, text):
    """Check that an assessment field contains specific text"""
    field_name = f"vereist_{assessment_type}"
    if field_name not in context.result.output:
        raise AssertionError(f"Field '{field_name}' not found in result: {context.result.output.keys()}")
    
    value = context.result.output[field_name]
    assertions.assertIsNotNone(value, f"Expected {field_name} to have a value, but it was None")
    assertions.assertIn(text, str(value), f"Expected {field_name} to contain '{text}', but it was '{value}'")


