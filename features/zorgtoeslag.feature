Feature: Berekening Zorgtoeslag 2025
  Als burger
  Wil ik weten of ik recht heb op zorgtoeslag
  Zodat ik de juiste toeslag kan ontvangen

  Background:
    Given de datum is "2024-02-01"
    And een persoon met BSN "999993653"

  Scenario: Persoon onder 18 heeft geen recht op zorgtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 2007-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende DJI detenties gegevens:
      | bsn       | status | inrichting_type |
      | 999993653 | VRIJ   | GEEN            |
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then is niet voldaan aan de voorwaarden

  Scenario: Persoon boven 18 heeft recht op zorgtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 2005-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST inkomen gegevens:
      | bsn       | box1  | box2 | box3 | buitenlands |
      | 999993653 | 79547 | 0    | 0    | 0           |
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then is het toeslagbedrag "1782.34" euro

  Scenario: Alleenstaande met laag inkomen heeft recht op zorgtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1998-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST inkomen gegevens:
      | bsn       | box1  | box2 | box3 | buitenlands |
      | 999993653 | 20000 | 0    | 0    | 0           |
    And de volgende BELASTINGDIENST vermogen gegevens:
      | bsn       | bezittingen | schulden |
      | 999993653 | 10000       | 0        |
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op zorgtoeslag
    And is het toeslagbedrag "1811.28" euro

  Scenario: Persoon met studiefinanciering heeft recht op zorgtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 2004-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST inkomen gegevens:
      | bsn       | box1  | box2 | box3 | buitenlands |
      | 999993653 | 15000 | 0    | 0    | 0           |
    And de volgende DUO inschrijvingen gegevens:
      | bsn       | onderwijstype |
      | 999993653 | WO            |
    And de volgende DUO studiefinanciering gegevens:
      | bsn       | aantal_studerend_gezin |
      | 999993653 | 0                      |
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op zorgtoeslag
    And is het toeslagbedrag "1813.71" euro
