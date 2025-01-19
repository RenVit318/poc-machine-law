# language: nl
Functionaliteit: Zorgtoeslag Berekening 2025
Als burger
Wil ik weten of ik recht heb op zorgtoeslag
Zodat ik de juiste toeslag kan ontvangen

  Achtergrond:
    Gegeven het is het jaar "2025"
    En een persoon met BSN "999993653"
    En de volgende brongegevens:
      | Service         | Law                         | Table                 | Field                  | Value      |
      | BRP             | wet_brp                     | personen              | geboortedatum          | 1986-01-01 |
      | BRP             | wet_brp                     | personen              | verblijfsadres         | Amsterdam  |
      | BRP             | wet_brp                     | relaties              | partnerschap_type      | GEEN       |
      | DJI             | penitentiaire_beginselenwet | detenties             | status                 | VRIJ       |
      | DJI             | penitentiaire_beginselenwet | detenties             | inrichting_type        | GEEN       |
      | DJI             | wet_forensische_zorg        | forensische_zorg      | zorgtype               | GEEN       |
      | DJI             | wet_forensische_zorg        | forensische_zorg      | juridische_titel       | GEEN       |
      | RVZ             | zvw                         | verzekeringen         | polis.status           | ACTIEF     |
      | RVZ             | zvw                         | verdragsverzekeringen | registratie.status     | INACTIEF   |
      | BELASTINGDIENST | wet_inkomstenbelasting      | inkomen               | box1                   | 12000000   |
      | BELASTINGDIENST | wet_inkomstenbelasting      | inkomen               | box2                   | 0          |
      | BELASTINGDIENST | wet_inkomstenbelasting      | inkomen               | box3                   | 0          |
      | BELASTINGDIENST | wet_inkomstenbelasting      | inkomen               | buitenlands            | 0          |
      | BELASTINGDIENST | wet_inkomstenbelasting      | vermogen              | bezittingen            | 12040000   |
      | BELASTINGDIENST | wet_inkomstenbelasting      | vermogen              | schulden               | 0          |
      | DUO             | wet_studiefinanciering      | studiefinanciering    | aantal_studerend_gezin | 0          |
      | DUO             | wet_studiefinanciering      | inschrijvingen        | onderwijstype          | GEEN       |

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
