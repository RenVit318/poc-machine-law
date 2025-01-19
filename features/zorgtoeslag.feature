# language: nl
Functionaliteit: Zorgtoeslag Berekening 2025
Als burger
Wil ik weten of ik recht heb op zorgtoeslag
Zodat ik de juiste toeslag kan ontvangen

  Achtergrond:
    Gegeven de datum is "2024-02-01"
    En een persoon met BSN "999993653"
    En de volgende brongegevens:
      | Service         | Table                 | Field                  | Value      |
      | BRP             | personen              | geboortedatum          | 1986-01-01 |
      | BRP             | personen              | verblijfsadres         | Amsterdam  |
      | BRP             | relaties              | partnerschap_type      | GEEN       |
      | DJI             | detenties             | status                 | VRIJ       |
      | DJI             | detenties             | inrichting_type        | GEEN       |
      | DJI             | forensische_zorg      | zorgtype               | GEEN       |
      | DJI             | forensische_zorg      | juridische_titel       | GEEN       |
      | RVZ             | verzekeringen         | polis.status           | ACTIEF     |
      | RVZ             | verdragsverzekeringen | registratie.status     | INACTIEF   |
      | BELASTINGDIENST | inkomen               | box1                   | 12000000   |
      | BELASTINGDIENST | inkomen               | box2                   | 0          |
      | BELASTINGDIENST | inkomen               | box3                   | 0          |
      | BELASTINGDIENST | inkomen               | buitenlands            | 0          |
      | BELASTINGDIENST | vermogen              | bezittingen            | 12040000   |
      | BELASTINGDIENST | vermogen              | schulden               | 0          |
      | DUO             | studiefinanciering    | aantal_studerend_gezin | 0          |
      | DUO             | inschrijvingen        | onderwijstype          | GEEN       |

  Scenario: Persoon jonger dan 18 heeft geen recht op zorgtoeslag
    Gegeven de persoon is "17" jaar oud
    En de persoon heeft een zorgverzekering
    Als de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Dan is niet voldaan aan de voorwaarden

  Scenario: Persoon ouder 18 heeft recht op zorgtoeslag
    Gegeven de persoon is "19" jaar oud
    Als de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Dan is het toeslagbedrag "1782.34" euro

  Scenario: Alleenstaande met laag inkomen heeft recht op zorgtoeslag
    Gegeven de persoon is "25" jaar oud
    En de persoon heeft een zorgverzekering
    En de persoon heeft geen toeslagpartner
    En de persoon heeft een inkomen van "20000" euro
    En de persoon heeft een vermogen van "10000" euro
    Als de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Dan heeft de persoon recht op zorgtoeslag
    En is voldaan aan de voorwaarden
    En is het toeslagbedrag hoger dan "0" euro

  Scenario: Alleenstaande met studiefinanciering heeft recht op zorgtoeslag
    Gegeven de persoon is "20" jaar oud
    En de persoon heeft een zorgverzekering
    En de persoon heeft geen toeslagpartner
    En de persoon heeft een inkomen van "15000" euro
    En de persoon heeft studiefinanciering van "4000" euro
    En de persoon heeft een vermogen van "10000" euro
    Als de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    Dan heeft de persoon recht op zorgtoeslag
    En is voldaan aan de voorwaarden
    En is het toeslagbedrag hoger dan "0" euro
