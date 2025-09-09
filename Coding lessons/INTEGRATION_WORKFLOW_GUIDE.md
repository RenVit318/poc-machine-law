# Integration and Workflow Guide

This guide provides a comprehensive overview of how to integrate new laws into the machine law system, covering the complete workflow from law definition to testing and deployment.

## Complete Integration Workflow

### Phase 1: Law Analysis and Planning

#### 1.1 Legal Research
```bash
# Before starting implementation
1. Obtain official legal text (BWB, wetten.overheid.nl)
2. Identify legal articles and requirements
3. Map dependencies to other laws/services
4. Determine calculation complexity level
5. Identify required data sources
```

#### 1.2 Technical Planning
- **Service Mapping**: Which government service will execute this law?
- **Data Requirements**: What external data is needed?
- **Output Definition**: What results should citizens/services receive?
- **Complexity Assessment**: Simple eligibility vs. complex calculations?

### Phase 2: Service and Infrastructure Setup

#### 2.1 Create Service Definition
```yaml
# /services/[SERVICE_NAME].yaml
uuid: [generate-uuid]
name: "[Service Display Name]"
endpoint: "http://localhost:[PORT]"
```

#### 2.2 Set up Mock Data Sources
```python
# In your test scenarios, define realistic government data
# Example: Mock RvIG (Civil Registry) data
Given de volgende RvIG personen gegevens:
  | bsn       | geboortedatum | nationaliteit |
  | 999993653 | 1990-01-01    | NEDERLANDS    |
```

### Phase 3: YAML Law Definition

#### 3.1 Create Law Specification
```bash
# Create directory structure
mkdir -p law/[law_domain]/
```

#### 3.2 Use YAML Template
Follow the comprehensive template in `YAML_LAW_TEMPLATE.md`:

1. **Header Section**: UUID, names, legal metadata
2. **Legal Basis**: BWB references and explanations  
3. **Properties Section**: Parameters, inputs, outputs, logic
4. **Validation**: Run schema validation

```bash
# Validate your YAML
./script/validate.py
```

### Phase 4: Test Case Development

#### 4.1 Create Feature File
```bash
# Create test file
touch features/[law_name].feature
```

#### 4.2 Use Gherkin Template
Follow patterns from `GHERKIN_TEST_TEMPLATE.md`:

1. **Feature Declaration**: User story format
2. **Background Setup**: Common data and dates
3. **Positive Scenarios**: Happy path testing
4. **Negative Scenarios**: Exclusion cases
5. **Edge Cases**: Boundary conditions

#### 4.3 Test Data Strategy
- Use consistent test BSNs (999xxxxxx format)
- Create realistic financial/personal data
- Cover all legal requirements and exclusions
- Include complex family/relationship scenarios

### Phase 5: Step Definition Implementation

#### 5.1 Check Existing Steps
```bash
# Search existing steps to avoid duplication
grep -r "step_impl" features/steps/
```

#### 5.2 Implement New Steps (if needed)
Follow patterns from `PYTHON_STEPS_GUIDE.md`:

1. **Data Setup Steps** (@given): Prepare test context
2. **Action Steps** (@when): Execute law evaluation
3. **Assertion Steps** (@then): Verify outcomes

#### 5.3 Integration Patterns
- Use existing `evaluate_law()` function
- Handle context management properly
- Implement proper error handling
- Add debugging support

### Phase 6: Testing and Validation

#### 6.1 Run Individual Tests
```bash
# Test specific feature
uv run behave features/[law_name].feature --no-capture -v
```

#### 6.2 Schema and Reference Validation
```bash
# Comprehensive validation
./script/validate.py

# Specific law validation
python -c "
from machine.utils import RuleResolver
resolver = RuleResolver()
law = resolver.get_law('[SERVICE]', '[LAW_NAME]')
print(f'Law loaded successfully: {law.name}')
"
```

#### 6.3 Integration Testing
```bash
# Run all tests to ensure no regressions
uv run behave features --no-capture -v --define log_level=DEBUG

# Code quality checks
ruff check
ruff format
pre-commit run --all-files
```

### Phase 7: Web Interface Integration

#### 7.1 Service Discovery
Laws marked with `discoverable: "CITIZEN"` automatically appear in:
- Web interface at http://0.0.0.0:8000
- Law inspector tool
- Citizen services portal

#### 7.2 Test Web Integration
```bash
# Start web interface
uv run web/main.py

# Access at http://0.0.0.0:8000
# Test law evaluation through UI
# Verify citizen-friendly explanations
```

### Phase 8: Performance and Simulation

#### 8.1 Population-Level Testing
```bash
# Run demographic simulations
uv run simulate.py

# Analyze impact on different population groups
# Verify performance with large datasets
```

#### 8.2 Service Performance
- Test cross-service dependencies
- Verify caching effectiveness
- Check memory usage with complex laws

## Key Integration Points

### 1. YAML ↔ Python Engine Integration

**RuleResolver System**:
```python
from machine.utils import RuleResolver

resolver = RuleResolver()
law_spec = resolver.get_law(service="TOESLAGEN", law="zorgtoeslagwet")
print(f"Law: {law_spec.name}, Valid from: {law_spec.valid_from}")
```

**Rule Evaluation**:
```python
from machine.service import Services

services = Services("2024-01-01")
result = services.evaluate(
    "TOESLAGEN",
    law="zorgtoeslagwet", 
    parameters={"BSN": "999993653"},
    reference_date="2024-01-01"
)
print(f"Output: {result.output}")
```

### 2. Gherkin ↔ Step Definitions Integration

**Context Flow**:
1. Gherkin table → `context.table`
2. Step function → `context.services.set_source_dataframe()`
3. Law execution → `context.result`
4. Assertions → `context.result.output`

**Data Processing Pipeline**:
```python
# In step definitions
def process_table_data(table):
    data = []
    for row in table:
        processed = {k: parse_value(v) for k, v in row.items()}
        data.append(processed)
    return pd.DataFrame(data)
```

### 3. Service ↔ Data Integration

**Mock Data Sources**:
- DataFrame-based government service simulation
- Realistic data relationships (BSN cross-references)
- Proper null handling and edge cases

**Real Service Integration** (future):
```yaml
# In service definitions
service: "RvIG"
endpoint: "https://api.rviq.nl/brp/v1"
authentication: "oauth2"
rate_limit: "1000/hour"
```

## Configuration and Dependencies

### 1. Environment Setup

**Required Python Version**: 3.12+

**Key Dependencies**:
```toml
# From pyproject.toml
behave = ">=1.2.6"          # BDD testing
pydantic = ">=2.10.5"       # Data validation
jsonschema = ">=4.23.0"     # YAML validation
fastapi = ">=0.115.8"       # Web framework
pandas = ">=2.2.3"          # Data processing
```

**Setup Commands**:
```bash
# Install dependencies
uv sync

# Setup pre-commit hooks
pre-commit install

# Validate setup
./script/validate.py
```

### 2. Development Configuration

**Code Quality Tools**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
```

**Testing Configuration**:
```python
# features/environment.py
def before_scenario(context, scenario):
    context.parameters = {}
    context.services = None
    context.result = None
```

### 3. Schema Validation

**JSON Schema Location**: `/schema/v0.1.5/schema.json`

**Validation Requirements**:
- All law YAML files must validate against schema
- Service references must resolve to existing services
- Field references must be properly defined
- Legal basis must include BWB references

## Quality Assurance Process

### 1. Automated Validation
```bash
# Pre-commit hooks run automatically
git commit -m "Add new law"

# Manual validation
pre-commit run --all-files
./script/validate.py
uv run behave features --no-capture
```

### 2. Code Review Checklist
- [ ] YAML follows schema v0.1.5
- [ ] Legal basis includes BWB ID and articles
- [ ] Test cases cover positive, negative, and edge cases
- [ ] Step definitions follow existing patterns
- [ ] Error handling is comprehensive
- [ ] Performance impact is acceptable

### 3. Integration Testing
- [ ] Law evaluates correctly in isolation
- [ ] Cross-service dependencies work
- [ ] Web interface displays law properly
- [ ] Simulation runs without errors
- [ ] No regressions in existing laws

## Best Practices for Maintainability

### 1. Documentation Standards
- Document legal reasoning in YAML explanations
- Include references to specific law articles
- Comment complex calculation logic
- Maintain clear commit messages

### 2. Naming Conventions
- **Files**: `[SERVICE]-[YYYY-MM-DD].yaml`
- **Variables**: `UPPER_SNAKE_CASE` for constants
- **Services**: Match official government abbreviations
- **Steps**: Clear, descriptive Dutch phrases

### 3. Modular Design
- Separate eligibility from calculation logic
- Reuse common step definitions
- Create helper functions for complex logic
- Maintain clear service boundaries

### 4. Version Management
- Use `valid_from` dates for law changes
- Maintain backwards compatibility
- Test version transitions
- Document breaking changes

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Schema Validation Errors
```bash
# Error: Invalid YAML structure
./script/validate.py
# Fix: Check JSON schema requirements

# Error: Reference not found
grep -r "UNDEFINED_FIELD" law/
# Fix: Define missing fields in properties section
```

#### 2. Test Execution Errors
```bash
# Error: Step definition not found
grep -r "Given.*step text" features/steps/
# Fix: Implement missing step or use existing pattern

# Error: Service not found
ls services/
# Fix: Create service YAML file
```

#### 3. Integration Issues
```bash
# Error: Law not loading
python -c "
from machine.utils import RuleResolver
resolver = RuleResolver()
print(resolver.discover_rules('[SERVICE]'))
"
# Fix: Check service and law name consistency
```

#### 4. Performance Problems
```bash
# Profile law evaluation
python -m cProfile -o profile.stats simulate.py
python -c "
import pstats
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative').print_stats(20)
"
```

## Deployment Considerations

### 1. Production Readiness
- Replace mock services with real government APIs
- Implement proper authentication and authorization
- Set up monitoring and logging
- Configure secure session management
- Enable HTTPS and security headers

### 2. Scalability Planning
- Design for concurrent law evaluations
- Plan for database backing of calculations
- Consider caching strategies for complex laws
- Plan for audit trail storage

### 3. Legal Compliance
- Ensure audit trails for all decisions
- Implement data retention policies
- Plan for law change management
- Establish legal review processes

This comprehensive guide provides the complete workflow for successfully integrating new laws into the machine law system while maintaining quality, consistency, and legal compliance.