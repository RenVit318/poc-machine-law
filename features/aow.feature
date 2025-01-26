Feature: AOW Pensioen Berekening 2025
  Als burger die de pensioenleeftijd nadert
  Wil ik weten of ik recht heb op AOW pensioen
  Zodat ik mijn pensioenfinanciën kan plannen

  Background:
    Given de datum is "2025-03-01"
    And een persoon met BSN "999993653"

  Scenario: Persoon met gemengde verzekeringsjaren ontvangt gedeeltelijk pensioen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1958-02-15    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende SVB verzekerde_tijdvakken gegevens:
      | bsn       | woonperiodes |
      | 999993653 | 35           |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 999993653 | 2012-01-01 | 2013-01-01 |
      | 999993653 | 2014-01-01 | 2024-01-01 |
    And de volgende UWV uitkeringen gegevens:
      | bsn       | start_date | end_date   | type |
      | 999993653 | 2012-01-01 | 2014-01-01 | WW   |
    And de volgende CBS levensverwachting gegevens:
      | bsn       | verwachting_65 |
      | 999993653 | 20.5           |
    When de algemene_ouderdomswet wordt uitgevoerd door SVB
    Then is voldaan aan de voorwaarden
    And is het pensioen "1324.80" euro
