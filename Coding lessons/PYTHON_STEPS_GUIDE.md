# Python Step Definitions Implementation Guide

This guide provides comprehensive patterns and best practices for implementing Python step definitions in the machine law system. Based on analysis of the existing codebase, this guide shows how to create maintainable, robust step definitions that integrate with the YAML law specifications.

## Architecture Overview

The step definitions in `/features/steps/steps.py` serve as the bridge between:
- **Gherkin scenarios** (human-readable test cases)
- **YAML law definitions** (machine-readable legal logic)
- **Services system** (data sources and rule evaluation)

### Key Components
- **Context object**: Stores scenario state and parameters
- **Services system**: Orchestrates law evaluation and data access
- **RuleResult objects**: Contains evaluation outcomes and traced execution
- **Assertion helpers**: Validate expected outcomes

## Basic Step Definition Patterns

### 1. Data Setup Steps (@given)

#### Personal Information Setup
```python
@given('een persoon met BSN "{bsn}"')
def step_impl(context, bsn):
    """Set the primary BSN for the scenario"""
    if not hasattr(context, "parameters"):
        context.parameters = {}
    context.parameters["BSN"] = bsn

@given('de datum is "{date}"')
def step_impl(context, date):
    """Set reference date and initialize services"""
    context.root_reference_date = date
    context.services = Services(date)
```

#### Data Source Setup Pattern
```python
@given("de volgende {service} {table} gegevens")
def step_impl(context, service, table):
    """Generic pattern for setting up data from any government service"""
    if not context.table:
        raise ValueError(f"No table provided for {service} {table}")
    
    # Convert Gherkin table to DataFrame with intelligent type parsing
    data = []
    for row in context.table:
        processed_row = {}
        for key, value in row.items():
            # Keep identifier fields as strings, parse others
            if key in {"bsn", "partner_bsn", "jaar", "kind_bsn", "werkgever"}:
                processed_row[key] = value if value != "null" else None
            else:
                processed_row[key] = parse_value(value)
        data.append(processed_row)
    
    df = pd.DataFrame(data)
    context.services.set_source_dataframe(service, table, df)
```

**Key features:**
- **Dynamic service/table extraction** from step text
- **Intelligent type parsing** preserving identifiers as strings
- **Null handling** for missing relationships
- **DataFrame integration** with pandas-based data processing

#### Complex Data Setup Pattern
```python
@given("de volgende {data_type} gegevens")
def step_impl(context, data_type):
    """Handle specific data types with custom processing"""
    if not context.table:
        raise ValueError(f"No table provided for {data_type}")
    
    if data_type == "kandidaatgegevens":
        # Example: Electoral candidate data with special processing
        data = []
        for row in context.table:
            processed_row = {
                "kandidaat_bsn": row["kandidaat_bsn"],
                "positie": int(row["positie"]) if row["positie"] != "..." else None,
                "acceptatie": parse_value(row["acceptatie"]),
            }
            # Skip placeholder rows
            if processed_row["positie"] is not None:
                data.append(processed_row)
        
        df = pd.DataFrame(data)
        # Store in test_data for user input override
        if not hasattr(context, "test_data"):
            context.test_data = {}
        
        context.test_data["CANDIDATE_LIST"] = df[["kandidaat_bsn", "positie"]]
        context.test_data["CANDIDATE_ACCEPTANCE"] = df["acceptatie"].iloc[0]
    else:
        raise NotImplementedError(f"Data type {data_type} not implemented")
```

### 2. Action Steps (@when)

#### Standard Law Execution
```python
@when("de {law} wordt uitgevoerd door {service}")
def step_impl(context, law, service):
    """Execute a law evaluation through the specified service"""
    evaluate_law(context, service, law)

def evaluate_law(context, service: str, law: str, approved: bool = True):
    """Centralized law evaluation with full context management"""
    try:
        context.result = context.services.evaluate(
            service,
            law=law,
            parameters=context.parameters,
            reference_date=context.root_reference_date,
            overwrite_input=getattr(context, "test_data", None),
            approved=approved
        )
        
        # Store metadata for later assertions
        context.service = service
        context.law = law
        
    except Exception as e:
        # Store exception for assertion checking
        context.evaluation_error = e
        context.result = None
```

#### Law Execution with User Input
```python
@when("de {law} wordt uitgevoerd door {service} met wijzigingen")
def step_impl(context, law, service):
    """Execute law with user-provided input corrections"""
    if not hasattr(context, "test_data"):
        context.test_data = {}
    
    # Process user input table if provided
    if hasattr(context, "table") and context.table:
        for row in context.table:
            key = list(row.headings)[0]  # Get first column as key
            value = row[key]
            
            # Parse JSON-like values
            if value.startswith('[') or value.startswith('{'):
                try:
                    value = json.loads(value.replace("'", '"'))
                except json.JSONDecodeError:
                    pass
            
            context.test_data[key] = value
    
    evaluate_law(context, service, law)
```

#### Process Flow Actions
```python
@when("de persoon dit aanvraagt")
def step_impl(context):
    """Submit a case for manual processing"""
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No law evaluation result to submit")
    
    case_id = context.services.case_manager.submit_case(
        bsn=context.parameters["BSN"],
        service_type=context.service,
        law=context.law,
        parameters=context.result.input,
        claimed_result=context.result.output,
        approved_claims_only=True
    )
    context.case_id = case_id

@when('de beoordelaar de aanvraag afwijst met reden "{reason}"')
def step_impl(context, reason):
    """Process manual rejection with specific reason"""
    if not hasattr(context, "case_id"):
        raise ValueError("No case to reject")
    
    case = context.services.case_manager.get_case_by_id(context.case_id)
    case.decide(
        verified_result=context.result.output,
        reason=reason,
        verifier_id="BEOORDELAAR",
        approved=False,
    )
    context.services.case_manager.save(case)
```

#### Data Correction Actions
```python
@when("de burger {action_type} indient")
def step_impl(context, action_type):
    """Handle citizen data corrections and claims"""
    if not context.table:
        raise ValueError(f"No table provided for {action_type}")
    
    if action_type in ["wijzigingen", "deze gegevens"]:
        if not hasattr(context, "claims"):
            context.claims = []
        
        for row in context.table:
            claim_id = context.services.claim_manager.submit_claim(
                service=row["service"],
                key=row["key"],
                new_value=parse_value(row["nieuwe_waarde"]),
                reason=row["reden"],
                claimant="BURGER",
                case_id=getattr(context, "case_id", None),
                evidence_path=row.get("bewijs"),
                law=row["law"],
                bsn=context.parameters["BSN"]
            )
            context.claims.append(claim_id)
    else:
        raise NotImplementedError(f"Action type {action_type} not implemented")
```

### 3. Assertion Steps (@then)

#### Eligibility Assertions
```python
@then("is voldaan aan de voorwaarden")
def step_impl(context):
    """Assert that all legal requirements are met"""
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No evaluation result to check")
    
    # Check for any boolean field indicating eligibility
    eligible_fields = [
        "is_eligible", "heeft_recht", "is_verzekerde", 
        "heeft_stemrecht", "is_qualified"
    ]
    
    for field in eligible_fields:
        if field in context.result.output:
            assertions.assertTrue(
                context.result.output[field],
                f"Expected to meet requirements, but {field} was {context.result.output[field]}"
            )
            return
    
    # If no standard eligibility field found, check requirements directly
    if hasattr(context.result, "requirements_met"):
        assertions.assertTrue(
            context.result.requirements_met,
            "Expected all requirements to be met, but they were not"
        )
    else:
        raise ValueError("Cannot determine eligibility status from result")

@then("is niet voldaan aan de voorwaarden")
def step_impl(context):
    """Assert that legal requirements are not met"""
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No evaluation result to check")
    
    # Inverse of the above logic
    eligible_fields = [
        "is_eligible", "heeft_recht", "is_verzekerde", 
        "heeft_stemrecht", "is_qualified"
    ]
    
    for field in eligible_fields:
        if field in context.result.output:
            assertions.assertFalse(
                context.result.output[field],
                f"Expected NOT to meet requirements, but {field} was {context.result.output[field]}"
            )
            return
    
    if hasattr(context.result, "requirements_met"):
        assertions.assertFalse(
            context.result.requirements_met,
            "Expected requirements NOT to be met, but they were"
        )
    else:
        raise ValueError("Cannot determine eligibility status from result")
```

#### Monetary Amount Assertions
```python
@then('is het toeslagbedrag "{amount}" euro')
def step_impl(context, amount):
    """Assert specific benefit amount in euros"""
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No evaluation result to check")
    
    # Try multiple common field names for benefit amounts
    amount_fields = ["hoogte_toeslag", "jaarbedrag", "toeslagbedrag", "bedrag"]
    actual_amount = None
    
    for field in amount_fields:
        if field in context.result.output:
            actual_amount = context.result.output[field]
            break
    
    if actual_amount is None:
        available_fields = list(context.result.output.keys())
        raise ValueError(
            f"No amount field found in output. Available fields: {available_fields}"
        )
    
    compare_euro_amount(actual_amount, amount)

@then('is het {field_name} "{expected_value}" eurocent')
def step_impl(context, field_name, expected_value):
    """Assert specific field value in eurocents"""
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No evaluation result to check")
    
    if field_name not in context.result.output:
        available_fields = list(context.result.output.keys())
        raise ValueError(
            f"Field {field_name} not found in output. Available fields: {available_fields}"
        )
    
    actual_value = context.result.output[field_name]
    expected_int = int(expected_value)
    
    assertions.assertEqual(
        actual_value,
        expected_int,
        f"Expected {field_name} to be {expected_value} eurocent, but was {actual_value} eurocent"
    )

def compare_euro_amount(actual_eurocent: int, expected_euro_str: str):
    """Helper to compare eurocent amounts with euro strings"""
    expected_eurocent = int(float(expected_euro_str) * 100)
    assertions.assertEqual(
        actual_eurocent,
        expected_eurocent,
        f"Expected amount to be {expected_euro_str} euros ({expected_eurocent} eurocent), "
        f"but was {actual_eurocent / 100:.2f} euros ({actual_eurocent} eurocent)"
    )
```

#### Process Status Assertions
```python
@then('is de status "{expected_status}"')
def step_impl(context, expected_status):
    """Assert case or process status"""
    if hasattr(context, "case_id"):
        case = context.services.case_manager.get_case_by_id(context.case_id)
        actual_status = case.status
    elif hasattr(context, "result") and "status" in context.result.output:
        actual_status = context.result.output["status"]
    else:
        raise ValueError("No status information available to check")
    
    assertions.assertEqual(
        actual_status,
        expected_status,
        f"Expected status to be '{expected_status}', but was '{actual_status}'"
    )

@then("ontbreken er verplichte gegevens")
def step_impl(context):
    """Assert that required data is missing"""
    if hasattr(context, "evaluation_error"):
        # Check if error is due to missing required data
        error_msg = str(context.evaluation_error).lower()
        missing_data_indicators = ["missing", "required", "ontbreekt", "verplicht"]
        
        if any(indicator in error_msg for indicator in missing_data_indicators):
            return  # Expected error occurred
        else:
            raise AssertionError(
                f"Expected missing data error, but got: {context.evaluation_error}"
            )
    else:
        raise ValueError("No evaluation error found, but expected missing data")

@then("ontbreken er geen verplichte gegevens")
def step_impl(context):
    """Assert that all required data is present"""
    if hasattr(context, "evaluation_error"):
        raise AssertionError(
            f"Expected no missing data, but got error: {context.evaluation_error}"
        )
    
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No evaluation result, suggesting missing data issue")
    
    # Success - we have a result and no errors
```

#### Complex Field Assertions
```python
@then('is het {field_name} "{expected_value}"')
def step_impl(context, field_name, expected_value):
    """Generic field value assertion with type-aware comparison"""
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

@then("bevat de uitkomst {field_name}")
def step_impl(context, field_name):
    """Assert that output contains a specific field"""
    if not hasattr(context, "result") or context.result is None:
        raise ValueError("No evaluation result to check")
    
    assertions.assertIn(
        field_name, 
        context.result.output,
        f"Expected output to contain field '{field_name}', but it was missing"
    )
```

## Utility Functions and Helpers

### Value Parsing Function
```python
def parse_value(value: str) -> Any:
    """Intelligent value parsing for various data types"""
    if value is None or value == "null":
        return None
    
    if isinstance(value, str):
        value = value.strip()
        
        # Handle empty strings
        if not value:
            return None
        
        # Handle boolean strings
        if value.lower() in ["true", "waar", "ja", "yes"]:
            return True
        elif value.lower() in ["false", "onwaar", "nee", "no"]:
            return False
        
        # Try JSON parsing for complex structures
        if value.startswith('[') or value.startswith('{'):
            try:
                return json.loads(value.replace("'", '"'))
            except json.JSONDecodeError:
                pass
        
        # Try numeric parsing
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
    
    # Return as string if no other parsing works
    return value
```

### Context Validation Helpers
```python
def ensure_context_attributes(context, *attributes):
    """Ensure required context attributes exist"""
    missing = []
    for attr in attributes:
        if not hasattr(context, attr):
            missing.append(attr)
    
    if missing:
        raise ValueError(f"Missing required context attributes: {missing}")

def get_output_field(context, *field_names):
    """Get first available field from result output"""
    ensure_context_attributes(context, "result")
    
    if context.result is None:
        raise ValueError("No evaluation result available")
    
    for field_name in field_names:
        if field_name in context.result.output:
            return context.result.output[field_name]
    
    available_fields = list(context.result.output.keys())
    raise ValueError(
        f"None of the fields {field_names} found in output. Available: {available_fields}"
    )
```

## Integration with YAML Law Definitions

### Service and Law Resolution
```python
def validate_service_and_law(service: str, law: str):
    """Validate that service and law combination exists"""
    # This would integrate with the RuleResolver system
    try:
        rule_resolver = RuleResolver()
        law_spec = rule_resolver.get_law(service, law)
        if law_spec is None:
            raise ValueError(f"Law {law} not found for service {service}")
        return law_spec
    except Exception as e:
        raise ValueError(f"Error validating service/law combination: {e}")
```

### Type System Integration
```python
def apply_type_spec(value: Any, type_spec: dict) -> Any:
    """Apply type specifications from YAML law definitions"""
    if not type_spec:
        return value
    
    # Handle currency conversion
    if type_spec.get("unit") == "eurocent":
        if isinstance(value, (int, float)):
            return int(value)  # Ensure integer eurocents
    
    # Handle precision
    if "precision" in type_spec and isinstance(value, float):
        return round(value, type_spec["precision"])
    
    # Handle min/max bounds
    if "min" in type_spec and value < type_spec["min"]:
        raise ValueError(f"Value {value} below minimum {type_spec['min']}")
    if "max" in type_spec and value > type_spec["max"]:
        raise ValueError(f"Value {value} above maximum {type_spec['max']}")
    
    return value
```

## Best Practices for Step Implementation

### 1. Error Handling and Validation
```python
@given("complex setup step")
def step_impl(context):
    try:
        # Validate inputs
        if not context.table:
            raise ValueError("Table data required for this step")
        
        # Process data with validation
        for row in context.table:
            validate_row_data(row)
        
        # Store results with error handling
        context.data = process_table_data(context.table)
        
    except Exception as e:
        # Provide context-specific error messages
        raise ValueError(f"Error in setup step: {e}") from e

def validate_row_data(row):
    """Validate individual row data"""
    required_fields = ["bsn", "service"]
    missing_fields = [field for field in required_fields if field not in row]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
```

### 2. Context Management
```python
@given("initialization step")
def step_impl(context):
    # Initialize context attributes safely
    if not hasattr(context, "parameters"):
        context.parameters = {}
    if not hasattr(context, "test_data"):
        context.test_data = {}
    
    # Store step-specific data
    context.current_step = "initialization"
```

### 3. Reusable Step Patterns
```python
# Generic data setup that can handle multiple table types
@given("de volgende {data_source} gegevens voor {subject_type}")
def step_impl(context, data_source, subject_type):
    """Flexible data setup for various sources and subjects"""
    setup_data_table(context, data_source, subject_type, context.table)

def setup_data_table(context, source: str, subject: str, table):
    """Reusable table processing logic"""
    if not table:
        raise ValueError(f"No table provided for {source} {subject}")
    
    # Convert based on known patterns
    df = convert_table_to_dataframe(table, source)
    context.services.set_source_dataframe(source, subject, df)
```

### 4. Debugging and Logging Support
```python
@then("debug output")
def step_impl(context):
    """Helper step for debugging test scenarios"""
    if hasattr(context, "result"):
        print(f"Result output: {context.result.output}")
        print(f"Result input: {context.result.input}")
        if hasattr(context.result, "trace"):
            print(f"Execution trace: {context.result.trace}")
    
    if hasattr(context, "services"):
        print(f"Available services: {list(context.services.services.keys())}")
```

## Adding New Step Definitions

### 1. Planning New Steps
Before implementing:
1. Check if existing generic steps can handle the scenario
2. Identify the specific legal domain requirements
3. Plan for reusability across similar laws
4. Consider error cases and edge conditions

### 2. Implementation Template
```python
@given("new step pattern with {parameter}")
def step_impl(context, parameter):
    """
    Brief description of what this step does
    
    Args:
        context: Behave context object
        parameter: Description of parameter
    """
    # Input validation
    if not parameter:
        raise ValueError("Parameter is required")
    
    # Context preparation
    if not hasattr(context, "custom_data"):
        context.custom_data = {}
    
    # Core logic
    try:
        result = process_step_logic(parameter)
        context.custom_data[parameter] = result
    except Exception as e:
        raise ValueError(f"Error processing {parameter}: {e}") from e

def process_step_logic(parameter):
    """Helper function for step logic"""
    # Implement the actual processing
    return {"processed": parameter}
```

### 3. Testing New Steps
```python
# Include test scenarios for your new steps
def test_new_step_function():
    """Unit test for step implementation"""
    # Create mock context
    context = MockContext()
    
    # Test normal operation
    step_impl(context, "test_parameter")
    assert hasattr(context, "custom_data")
    
    # Test error conditions
    with pytest.raises(ValueError):
        step_impl(context, "")
```

This comprehensive guide provides the foundation for implementing robust, maintainable step definitions that integrate seamlessly with the machine law system's YAML specifications and service architecture.