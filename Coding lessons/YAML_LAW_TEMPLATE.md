# YAML Law Definition Template

This template provides a comprehensive structure for defining new laws in the machine law system. Based on analysis of existing laws in the repository, this template is designed to be generic and applicable across different legal domains.

## Basic Template Structure

```yaml
# JSON Schema validation reference (keep this line exactly as-is)
$id: https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.5/schema.json

# Unique identifier for this law (generate with: python -c "import uuid; print(uuid.uuid4())")
uuid: [GENERATE_UUID]

# Human-readable name for the law
name: "[LAW_DISPLAY_NAME]"

# Machine-readable law identifier (use snake_case)
law: "[law_machine_name]"

# Legal classification (standard values)
law_type: "FORMELE_WET"
legal_character: "BESCHIKKING"  # or "BESLUIT_VAN_ALGEMENE_STREKKING"
decision_type: "TOEKENNING"     # or "AANSLAG" or "ALGEMEEN_VERBINDEND_VOORSCHRIFT"

# Visibility setting
discoverable: "CITIZEN"  # or "PROFESSIONAL" or "INTERNAL"

# Effective date (YYYY-MM-DD format)
valid_from: "YYYY-MM-DD"

# Executing government service (must match service in /services/)
service: "[SERVICE_NAME]"

# Human description of what this law does
description: "[Clear description of law's purpose and scope]"

# Legal basis and references
legal_basis:
  law: "[Full official law name]"
  bwb_id: "[Official BWB identifier from wetten.overheid.nl]"
  article: "[Specific article/section]"
  url: "[URL to official law text]"
  juriconnect: "[Juriconnect reference if available]"
  explanation: "[Human-readable explanation of legal basis]"

# Core law logic
properties:
  # Required input parameters
  parameters:
    - name: "BSN"
      description: "BSN van de betrokken persoon"
      type: "string"
      required: true
      legal_basis:
        law: "[Legal basis for requiring BSN]"
        article: "[Article requiring identification]"
        explanation: "[Why BSN is needed for this law]"
    
    # Add additional parameters as needed
    - name: "[PARAMETER_NAME]"
      description: "[Parameter description]"
      type: "[string|number|boolean|date|amount|array|object]"
      required: [true|false]
      legal_basis:
        law: "[Legal basis]"
        article: "[Article]"
        explanation: "[Explanation]"

  # External data sources (database tables, registrations)
  sources:
    - name: "[SOURCE_NAME]"
      description: "[Description of data source]"
      type: "[array|object]"
      source_reference:
        table: "[table_name]"
        fields: ["[field1]", "[field2]", "[field3]"]
        select_on:
          - name: "[selection_field]"
            value: "$[PARAMETER_REFERENCE]"

  # Service dependencies (data from other government services)
  input:
    - name: "[INPUT_FIELD_NAME]"
      description: "[Description of input field]"
      type: "[string|number|boolean|date|amount|array|object]"
      service_reference:
        service: "[SERVICE_NAME]"  # e.g., "RvIG", "BELASTINGDIENST"
        field: "[remote_field_name]"
        law: "[remote_law_name]"
        parameters:
          - name: "[param_name]"
            reference: "$[PARAMETER_REFERENCE]"
      # Optional: type specifications
      type_spec:
        unit: "[eurocent|euro|days|months|years]"
        precision: [0|1|2]
        min: [minimum_value]
        max: [maximum_value]
      # Optional: temporal specifications for date-sensitive data
      temporal:
        type: "[point_in_time|period]"
        period_type: "[year|month|continuous]"
        reference: "$[date_reference]"
        immutable_after: "[ISO_8601_duration]"
      legal_basis:
        law: "[Legal basis]"
        article: "[Article]"
        explanation: "[Explanation]"

  # Expected outputs
  output:
    - name: "[OUTPUT_FIELD_NAME]"
      description: "[Description of output]"
      type: "[string|number|boolean|date|amount|array|object]"
      citizen_relevance: "[primary|secondary|internal]"  # How important for citizens
      type_spec:
        unit: "[eurocent|euro|percentage]"
        precision: [0|1|2]
        min: [minimum_value]
        max: [maximum_value]
      legal_basis:
        law: "[Legal basis]"
        article: "[Article]"
        explanation: "[Explanation]"

  # Constants and reusable values
  definitions:
    # Use UPPER_SNAKE_CASE for constants
    MINIMUM_AGE: [18]
    MAXIMUM_AMOUNT: [500000]  # amounts in eurocents
    VALID_STATUSES:
      - "ACTIVE"
      - "PENDING"
      - "APPROVED"
    # Date constants
    REFERENCE_DATE: "2024-01-01"

  # Eligibility requirements (logical conditions)
  requirements:
    - all:  # All conditions must be true
        - subject: "$[INPUT_FIELD]"
          operation: "GREATER_OR_EQUAL"
          value: "$MINIMUM_AGE"
        - or:  # At least one of these conditions must be true
            - subject: "$[BOOLEAN_FIELD]"
              operation: "EQUALS"
              value: true
            - operation: "IN"
              subject: "$[STATUS_FIELD]"
              values: "$VALID_STATUSES"
    
    # Alternative: Simple requirement
    - subject: "$[INPUT_FIELD]"
      operation: "[EQUALS|GREATER_THAN|LESS_THAN|GREATER_OR_EQUAL|LESS_OR_EQUAL|IN|NOT_IN]"
      value: "[comparison_value]"

  # Actions (calculations and output assignments)
  actions:
    # Simple assignment
    - output: "[output_field_name]"
      operation: "ASSIGN"
      value: "$[input_reference_or_constant]"
    
    # Mathematical operations
    - output: "[calculated_field]"
      operation: "[ADD|SUBTRACT|MULTIPLY|DIVIDE|MIN|MAX|SUM]"
      values:
        - "$[input_field1]"
        - "$[input_field2]"
        - "[constant_value]"
    
    # Conditional logic
    - output: "[conditional_output]"
      operation: "IF"
      conditions:
        - subject: "$[test_field]"
          operation: "GREATER_THAN"
          value: "[threshold]"
      then:
        - operation: "[MULTIPLY|ADD|etc]"
          values:
            - "$[field1]"
            - "[rate]"
      else:
        - operation: "ASSIGN"
          value: 0
    
    # Date calculations
    - output: "[date_result]"
      operation: "SUBTRACT_DATE"
      values:
        - "$[date_field1]"
        - "$[date_field2]"
      unit: "[days|months|years]"
```

## Template Variations by Law Complexity

### 1. Simple Eligibility Laws
For binary yes/no decisions (like voting rights):
- Focus on `requirements` section
- Boolean outputs with `citizen_relevance: primary`
- Minimal calculations in `actions`

### 2. Amount Calculation Laws
For benefit/tax calculations:
- Complex `actions` with mathematical operations
- Multiple `input` dependencies
- Amount outputs with proper `type_spec`

### 3. Progressive Rate Laws
For tax brackets or tiered benefits:
- Use `IF` operations in `actions`
- Define rate tables in `definitions`
- Multiple conditional branches

### 4. Cross-Service Integration Laws
For laws requiring multiple government agencies:
- Multiple `service_reference` entries
- Complex `requirements` with OR/AND logic
- Comprehensive `legal_basis` documentation

## Key Guidelines

### Legal Traceability
- **Always include legal_basis** for all fields that implement legal requirements
- **Use official BWB IDs** from wetten.overheid.nl
- **Reference specific articles** not just law names
- **Provide human explanations** for complex legal concepts

### Technical Standards
- **File naming**: `[SERVICE]-[YYYY-MM-DD].yaml`
- **Field naming**: Use `UPPER_SNAKE_CASE` for constants, lowercase for variables
- **Amounts**: Always use eurocents (1 euro = 100 eurocents)
- **Dates**: ISO 8601 format (YYYY-MM-DD)
- **Services**: Must match entries in `/services/` directory

### Schema Compliance
- **Required fields**: uuid, name, law, valid_from, service, description, properties
- **Type validation**: Use proper types and type_spec when needed
- **Reference validation**: All `$references` must resolve to defined fields

### Best Practices
1. **Start simple** - implement basic eligibility before complex calculations
2. **Test early** - create Gherkin scenarios alongside YAML definition
3. **Document thoroughly** - legal complexity requires clear explanations
4. **Version properly** - use effective dates for law changes
5. **Validate schema** - run `./script/validate.py` before committing

## Examples of Real Patterns

Refer to these existing laws for concrete examples:
- `/law/kieswet/` - Simple eligibility
- `/law/zorgtoeslag/` - Complex calculations with multiple services
- `/law/algemene_ouderdomswet/` - Progressive rates and date calculations
- `/law/participatiewet/` - Cross-service dependencies