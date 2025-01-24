Feature: Healthcare Allowance Calculation 2025
  As a citizen
  I want to know if I am eligible for healthcare allowance
  So that I can receive the correct allowance

  Background:
    Given de datum is "2024-02-01"
    And een persoon met BSN "999993653"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1986-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende DJI detenties gegevens:
      | bsn       | status | inrichting_type |
      | 999993653 | VRIJ   | GEEN            |
    And de volgende DJI forensische_zorg gegevens:
      | bsn       | zorgtype | juridische_titel |
      | 999993653 | GEEN     | GEEN             |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende RVZ verdragsverzekeringen gegevens:
      | bsn       | registratie.status |
      | 999993653 | INACTIEF           |
    And de volgende BELASTINGDIENST inkomen gegevens:
      | bsn       | box1  | box2 | box3 | buitenlands |
      | 999993653 | 79547 | 0    | 0    | 0           |
    And de volgende BELASTINGDIENST vermogen gegevens:
      | bsn       | bezittingen | schulden |
      | 999993653 | 1200000     | 0        |
    And de volgende DUO studiefinanciering gegevens:
      | bsn       | aantal_studerend_gezin |
      | 999993653 | 0                      |
    And de volgende DUO inschrijvingen gegevens:
      | bsn       | onderwijstype |
      | 999993653 | GEEN          |

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
