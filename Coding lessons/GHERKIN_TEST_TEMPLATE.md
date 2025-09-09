# Gherkin Test Case Template

This template provides comprehensive patterns for creating Gherkin feature files to test laws in the machine law system. Based on analysis of existing feature files, these patterns are designed to be reusable across different legal domains.

## Basic Feature File Structure

```gherkin
Feature: [Law Name/Calculation Type]
  Als [user role - typically "burger" for citizen]
  Wil ik [desired outcome - what the user wants to achieve]
  Zodat ik [business value/reason - why this matters to the user]

  Background:
    Given de datum is "[YYYY-MM-DD]"
    And een persoon met BSN "[TEST_BSN]"

  # Basic positive scenario
  Scenario: [Descriptive name for positive case]
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | [TEST_BSN] | [BIRTH_DATE]  | [CITY]        | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | [TEST_BSN] | [GEEN|PARTNER]   | [null|BSN]  |
    # Add other data sources as needed
    When de [law_name] wordt uitgevoerd door [SERVICE_NAME]
    Then is voldaan aan de voorwaarden
    And [specific positive assertions]

  # Basic negative scenario
  Scenario: [Descriptive name for negative case]
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | [TEST_BSN] | [BIRTH_DATE]  | [CITY]        | NEDERLAND     | NEDERLANDS    |
    # Setup that should fail requirements
    When de [law_name] wordt uitgevoerd door [SERVICE_NAME]
    Then is niet voldaan aan de voorwaarden
```

## Data Setup Patterns

### 1. Personal Information (RvIG - Civil Registry)
```gherkin
Given de volgende RvIG personen gegevens:
  | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit | geslacht |
  | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     | NEDERLANDS    | V        |
```

**Common field patterns:**
- `bsn`: Always use test BSNs (999xxxxxx format)
- `geboortedatum`: YYYY-MM-DD format
- `verblijfsadres`: City name
- `land_verblijf`: Country code (NEDERLAND, DUITSLAND, etc.)
- `nationaliteit`: Nationality (NEDERLANDS, etc.)
- `geslacht`: M/V/X for gender

### 2. Relationship Status (RvIG Relations)
```gherkin
Given de volgende RvIG relaties gegevens:
  | bsn       | partnerschap_type | partner_bsn | kinderen                                     |
  | 999993653 | GEEN              | null        | []                                           |
  | 888888888 | PARTNER           | 777777777   | [{"bsn": "111111111"}, {"bsn": "222222222"}] |
```

**Relationship types:**
- `GEEN`: Single/no partner
- `PARTNER`: Has partner
- `GESCHEIDEN`: Divorced
- `WEDUWE`: Widowed

### 3. Financial Data (Tax Service)
```gherkin
# Income tax data (Box 1 - employment/benefits)
Given de volgende BELASTINGDIENST box1 gegevens:
  | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming |
  | 999993653 | 4800000                   | 0                         | 0                     |

# Investment income (Box 3)
Given de volgende BELASTINGDIENST box3 gegevens:
  | bsn       | vermogen | rendement |
  | 999993653 | 100000   | 2500      |

# Property ownership
Given de volgende BELASTINGDIENST eigenwoninggegevens:
  | bsn       | woz_waarde | eigenwoningschuld |
  | 999993653 | 35000000   | 25000000         |
```

**Amount conventions:**
- All monetary values in **eurocents** (100 = €1.00)
- Use realistic amounts for test scenarios
- Consider edge cases (0, maximum values, negative amounts)

### 4. Employment Data (UWV - Employment Office)
```gherkin
Given de volgende UWV dienstverbanden gegevens:
  | bsn       | werkgever           | loon_per_maand | aantal_uren_per_week | start_datum | eind_datum |
  | 999993653 | Gemeente Amsterdam  | 400000         | 40                   | 2020-01-01  | null       |
```

### 5. Insurance Data (Healthcare/Benefits)
```gherkin
Given de volgende ZORGINSTITUUT verzekeringen gegevens:
  | bsn       | verzekerd | zorgverzekeraar | premie_per_maand |
  | 999993653 | true      | CZ              | 13000            |

Given de volgende TOESLAGEN zorgtoeslag gegevens:
  | bsn       | recht_op_zorgtoeslag | maandelijkse_premie |
  | 999993653 | true                 | 13000               |
```

### 6. Housing Data
```gherkin
Given de volgende kadaster woongegevens:
  | bsn       | huurprijs | woningtype | stad      | eigenaar |
  | 999993653 | 100000    | HUURWONING | Amsterdam | false    |
```

## Law Execution Patterns

### 1. Standard Law Execution
```gherkin
When de [law_name] wordt uitgevoerd door [SERVICE_NAME]
```

**Examples:**
- `When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN`
- `When de kieswet wordt uitgevoerd door KIESRAAD`
- `When de algemene_ouderdomswet wordt uitgevoerd door SVB`

### 2. Law Execution with User Input
```gherkin
When de [law_name] wordt uitgevoerd door [SERVICE] met wijzigingen
```

Use this when the citizen provides additional information.

### 3. Process Flow Execution
```gherkin
When de persoon dit aanvraagt
When de beoordelaar de aanvraag afwijst met reden "[reason]"
When de burger bezwaar maakt met reden "[reason]"
```

## Assertion Patterns

### 1. Eligibility Assertions
```gherkin
# Positive eligibility
Then is voldaan aan de voorwaarden
Then heeft de persoon recht op [toeslag_type]
Then heeft de persoon stemrecht

# Negative eligibility
Then is niet voldaan aan de voorwaarden
Then heeft de persoon geen recht op [toeslag_type]
Then heeft de persoon geen stemrecht
```

### 2. Monetary Amount Assertions
```gherkin
# Euro amounts (converted from eurocents)
Then is het toeslagbedrag "[amount]" euro
Then is het pensioen "[amount]" euro

# Exact eurocent amounts
Then is het [field_name] "[amount]" eurocent

# Percentage assertions
Then is het percentage "[percentage]" procent
```

**Examples:**
- `Then is het toeslagbedrag "194.83" euro`
- `Then is het hoogte_toeslag "19483" eurocent`

### 3. Process Status Assertions
```gherkin
Then is de status "DECIDED"
Then wordt de aanvraag toegevoegd aan handmatige beoordeling
Then ontbreken er verplichte gegevens
Then ontbreken er geen verplichte gegevens
```

### 4. Complex Field Assertions
```gherkin
Then is het [field_name] "[expected_value]"
Then bevat de uitkomst "[field_name]"
Then is de waarde van "[field_name]" gelijk aan "[expected_value]"
```

## Test Case Types and Patterns

### 1. Positive Test Cases (Happy Path)
```gherkin
Scenario: [Standard eligible case description]
  Given [person meets all criteria]
  And [has required financial/personal data]
  When de [law] wordt uitgevoerd door [SERVICE]
  Then is voldaan aan de voorwaarden
  And [specific positive outcomes]
```

### 2. Negative Test Cases (Exclusions)
```gherkin
Scenario: [Specific exclusion reason]
  Given [person fails specific criteria]
  When de [law] wordt uitgevoerd door [SERVICE]
  Then is niet voldaan aan de voorwaarden

# Age-based exclusion
Scenario: Persoon onder [age] heeft geen recht op [benefit]
  Given de volgende RvIG personen gegevens:
    | bsn       | geboortedatum | 
    | 999993653 | [TOO_YOUNG]   |
  When de [law] wordt uitgevoerd door [SERVICE]
  Then is niet voldaan aan de voorwaarden

# Income-based exclusion
Scenario: Persoon met te hoog inkomen krijgt geen [benefit]
  Given [high income data setup]
  When de [law] wordt uitgevoerd door [SERVICE]
  Then is niet voldaan aan de voorwaarden
```

### 3. Edge Case Testing
```gherkin
# Boundary testing
Scenario: Persoon precies [age] jaar krijgt wel/geen [benefit]
  Given [exact age boundary setup]
  When de [law] wordt uitgevoerd door [SERVICE]
  Then [expected boundary result]

# Complex family situations
Scenario: Persoon met [special_circumstance]
  Given [complex relationship/family setup]
  When de [law] wordt uitgevoerd door [SERVICE]
  Then [expected complex outcome]
```

### 4. Process Flow Testing
```gherkin
Scenario: Volledige aanvraag- en bezwaarprocedure
  Given [initial setup]
  When de persoon dit aanvraagt
  Then is de status "SUBMITTED"
  
  When de beoordelaar de aanvraag afwijst met reden "[rejection_reason]"
  Then is de status "REJECTED"
  
  When de burger bezwaar maakt met reden "[objection_reason]"
  Then is de status "UNDER_APPEAL"
  
  When de bezwaarcommissie de aanvraag goedkeurt
  Then is de status "APPROVED"
  And [final positive outcomes]
```

### 5. Data Correction Testing
```gherkin
Scenario: Burger corrigeert ontbrekende gegevens
  Given [incomplete initial data]
  When de [law] wordt uitgevoerd door [SERVICE] met wijzigingen
  Then ontbreken er verplichte gegevens
  
  When de burger deze gegevens indient:
    | service   | law     | key           | nieuwe_waarde | reden               |
    | [SERVICE] | [LAW]   | [FIELD_NAME]  | [VALUE]       | [CORRECTION_REASON] |
  Then ontbreken er geen verplichte gegevens
  And [successful outcome after correction]
```

## Complex Data Patterns

### 1. User Input Correction Table
```gherkin
When de burger deze gegevens indient:
  | service   | law              | key               | nieuwe_waarde | reden               |
  | TOESLAGEN | wet_kinderopvang | HUURPRIJS         | 72000         | verplichte gegevens |
  | RvIG      | wet_brp          | PARTNERSCHAP_TYPE | GEEN          | statuswijziging     |
```

### 2. JSON-like Complex Data
```gherkin
Given de volgende RvIG relaties gegevens:
  | bsn       | kinderen                                     |
  | 888888888 | [{"bsn": "111111111"}, {"bsn": "222222222"}] |
```

### 3. Multi-Year Data
```gherkin
Given de volgende BELASTINGDIENST box1 gegevens:
  | bsn       | jaar | loon_uit_dienstbetrekking |
  | 999993653 | 2023 | 4800000                   |
  | 999993653 | 2024 | 5200000                   |
```

## Law-Specific Patterns

### 1. Benefit Calculation Laws (Zorgtoeslag, Huurtoeslag, etc.)
Focus on:
- Income thresholds and benefit calculations
- Family composition effects
- Housing costs and regional differences
- Precise monetary assertions

```gherkin
Feature: Berekening [Benefit Name]
  Als burger
  Wil ik weten hoeveel [benefit] ik krijg
  Zodat ik mijn budget kan plannen

  Scenario: Standaard berekening [benefit]
    Given [income and personal data]
    When de [law] wordt uitgevoerd door [SERVICE]
    Then is het toeslagbedrag "[exact_amount]" euro
```

### 2. Eligibility Laws (Voting, Citizenship, etc.)
Focus on:
- Binary yes/no decisions
- Age, residency, and legal status requirements
- Exception cases and special circumstances

```gherkin
Feature: Bepaling [Eligibility Type]
  Als burger
  Wil ik weten of ik recht heb op [right/service]
  Zodat ik [can take appropriate action]

  Scenario: [Eligible case]
    Given [qualifying criteria]
    When de [law] wordt uitgevoerd door [SERVICE]
    Then heeft de persoon [right/eligibility]
```

### 3. Tax Laws
Focus on:
- Progressive rate calculations
- Deductions and exemptions
- Multi-source income integration

```gherkin
Feature: Berekening [Tax Type]
  Als belastingplichtige
  Wil ik mijn [tax] berekenen
  Zodat ik weet hoeveel ik moet betalen

  Scenario: [Tax calculation scenario]
    Given [income and deduction data]
    When de [tax_law] wordt uitgevoerd door BELASTINGDIENST
    Then is het [tax_field] "[amount]" eurocent
```

## Best Practices for Test Creation

### 1. Data Consistency
- Use consistent test BSNs (999xxxxxx format)
- Maintain realistic relationships between data fields
- Use proper date formats and realistic amounts

### 2. Scenario Naming
- Use descriptive Dutch scenario names
- Include the key distinguishing factor
- Be specific about test conditions

### 3. Coverage Strategy
- Test happy path first
- Cover all major exclusion criteria
- Include boundary conditions
- Test complex family/relationship scenarios
- Cover data correction workflows

### 4. Assertion Strategy
- Test both process outcome (eligible/not eligible)
- Verify specific calculated amounts
- Check intermediate calculation steps when relevant
- Validate process states for workflow laws

### 5. Test Data Management
- Use Background for common setup
- Create realistic but edge-case data
- Document why specific test values were chosen
- Ensure test data doesn't accidentally change over time

This template provides a comprehensive foundation for creating thorough, maintainable Gherkin test scenarios for any legal domain in the machine law system.