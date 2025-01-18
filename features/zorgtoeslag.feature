# language: nl
Functionaliteit: Zorgtoeslag Berekening 2025
Als burger
Wil ik weten of ik recht heb op zorgtoeslag
Zodat ik de juiste toeslag kan ontvangen

  Achtergrond:
    Gegeven het is het jaar "2025"
    En een persoon met BSN "999993653"

  Scenario: Persoon jonger dan 18 heeft geen recht op zorgtoeslag
    Gegeven de persoon is "17" jaar oud
    En de persoon heeft een zorgverzekering
    Als de zorgtoeslag wordt berekend
    Dan is niet voldaan aan de voorwaarden

  Scenario: Persoon jonger ouder 18 heeft recht op zorgtoeslag
    Gegeven de persoon is "19" jaar oud
    Als de zorgtoeslag wordt berekend
    Dan is het toeslagbedrag "1782.34" euro

  Scenario: Alleenstaande met laag inkomen heeft recht op zorgtoeslag
    Gegeven de persoon is "25" jaar oud
    En de persoon heeft een zorgverzekering
    En de persoon heeft geen toeslagpartner
    En de persoon heeft een inkomen van "20000" euro
    En de persoon heeft een vermogen van "10000" euro
    Als de zorgtoeslag wordt berekend
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
    Als de zorgtoeslag wordt berekend
    Dan heeft de persoon recht op zorgtoeslag
    En is voldaan aan de voorwaarden
    En is het toeslagbedrag hoger dan "0" euro
