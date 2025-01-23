Feature: Healthcare Allowance Calculation 2025
  As a citizen
  I want to know if I am eligible for healthcare allowance
  So that I can receive the correct allowance

  Background:
    Given de datum is "2024-02-01"
    And een persoon met BSN "999993653"
    And de volgende brongegevens:
      | Service         | Table                 | Field                  | BSN       | Value      |
      | RvIG            | personen              | geboortedatum          | 999993653 | 1986-01-01 |
      | RvIG            | personen              | verblijfsadres         | 999993653 | Amsterdam  |
      | RvIG            | personen              | land_verblijf          | 999993653 | NEDERLAND  |
      | RvIG            | relaties              | partnerschap_type      | 999993653 | GEEN       |
      | RvIG            | relaties              | partner_bsn            | 999993653 | null       |
      | DJI             | detenties             | status                 | 999993653 | VRIJ       |
      | DJI             | detenties             | inrichting_type        | 999993653 | GEEN       |
      | DJI             | forensische_zorg      | zorgtype               | 999993653 | GEEN       |
      | DJI             | forensische_zorg      | juridische_titel       | 999993653 | GEEN       |
      | RVZ             | verzekeringen         | polis_status           | 999993653 | ACTIEF     |
      | RVZ             | verdragsverzekeringen | registratie.status     | 999993653 | INACTIEF   |
      | BELASTINGDIENST | inkomen               | box1                   | 999993653 | 79547      |
      | BELASTINGDIENST | inkomen               | box2                   | 999993653 | 0          |
      | BELASTINGDIENST | inkomen               | box3                   | 999993653 | 0          |
      | BELASTINGDIENST | inkomen               | buitenlands            | 999993653 | 0          |
      | BELASTINGDIENST | vermogen              | bezittingen            | 999993653 | 1200000    |
      | BELASTINGDIENST | vermogen              | schulden               | 999993653 | 0          |
      | DUO             | studiefinanciering    | aantal_studerend_gezin | 999993653 | 0          |
      | DUO             | inschrijvingen        | onderwijstype          | 999993653 | GEEN       |

  Scenario: Person under 18 is not eligible for healthcare allowance
    Given de persoon is "17" jaar oud
    And de persoon heeft een zorgverzekering
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then is niet voldaan aan de voorwaarden

  Scenario: Person over 18 is eligible for healthcare allowance
    Given de persoon is "19" jaar oud
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then is het toeslagbedrag "1782.34" euro

  Scenario: Single person with low income is eligible for healthcare allowance
    Given de persoon is "25" jaar oud
    And de persoon heeft een zorgverzekering
    And de persoon heeft geen toeslagpartner
    And de persoon heeft een inkomen van "20000" euro
    And de persoon heeft een vermogen van "10000" euro
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op zorgtoeslag
    And is voldaan aan de voorwaarden
    And is het toeslagbedrag hoger dan "0" euro
    And is het toeslagbedrag "849.00" euro

  Scenario: Single person with student finance is eligible for healthcare allowance
    Given de persoon is "20" jaar oud
    And de persoon heeft een zorgverzekering
    And de persoon heeft geen toeslagpartner
    And de persoon heeft een inkomen van "15000" euro
    And de persoon heeft studiefinanciering van "4000" euro
    And de persoon heeft een vermogen van "10000" euro
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op zorgtoeslag
    And is voldaan aan de voorwaarden
    And is het toeslagbedrag hoger dan "0" euro
    And is het toeslagbedrag "1092.00" euro
