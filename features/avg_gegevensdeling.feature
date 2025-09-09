Feature: AVG Gegevensdeling tussen Organisaties
  Als verwerkingsverantwoordelijke
  Wil ik weten of gegevensdeling tussen organisaties is toegestaan onder de AVG
  Zodat ik GDPR-compliant kan handelen en privacy kan beschermen

  Background:
    Given de datum is "2025-01-01"
    And een aanvraag met ID "REQ-001"

  # Happy Path - Automatische goedkeuring: wettelijke verplichting
  Scenario: Gegevensdeling toegestaan op basis van wettelijke verplichting
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking              | wettelijke_verplichting_ref |
      | REQ-001     | WETTELIJKE_VERPLICHTING| Fraude detectie en preventie | Art. 52 Wwft                |
    And de volgende data categorieën:
      | aanvraag_id | data_categories        | aantal_betrokkenen | doel_omschrijving     |
      | REQ-001     | ["NAAM", "EMAIL"]      | 75                 | Fraudepreventie       |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is voldaan aan de voorwaarden
    And is het automatisch_toegestaan "true"
    And is het automatisch_geweigerd "false"
    And is het menselijke_beoordeling_nodig "false"
    And is het technische_voorwaarden_ok "true"
    And is het bevat_bijzondere_categorien "false"

  # Happy Path - Automatische goedkeuring: vitaal belang
  Scenario: Gegevensdeling toegestaan wegens vitaal belang
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking    |
      | REQ-001     | VITAAL_BELANG        | Medische noodhulp  |
    And de volgende data categorieën:
      | aanvraag_id | data_categories           | aantal_betrokkenen | doel_omschrijving |
      | REQ-001     | ["NAAM", "TELEFOONNUMMER"]| 1                  | Noodmelding       |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is voldaan aan de voorwaarden
    And is het automatisch_toegestaan "true"
    And is het menselijke_beoordeling_nodig "false"

  # Automatische weigering - Onvoldoende beveiliging
  Scenario: Gegevensdeling geweigerd wegens onvoldoende versleuteling
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking |
      | REQ-001     | WETTELIJKE_VERPLICHTING| Compliance      |
    And de volgende data categorieën:
      | aanvraag_id | data_categories    | aantal_betrokkenen | doel_omschrijving |
      | REQ-001     | ["NAAM", "ADRES"]  | 50                 | Verificatie       |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | false      | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het technische_voorwaarden_ok "false"
    And is het afwijzing_reden "Technische beveiligingsmaatregelen voldoen niet aan artikel 32.1 AVG (versleuteling, toegangscontroles, auditlogging vereist)"

  # Automatische weigering - Bijzondere categorieën zonder juiste grondslag
  Scenario: Gegevensdeling geweigerd wegens bijzondere categorieën zonder toestemming
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking |
      | REQ-001     | WETTELIJKE_VERPLICHTING| Onderzoek       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories                      | aantal_betrokkenen | doel_omschrijving    |
      | REQ-001     | ["NAAM", "GEZONDHEIDSGEGEVENS"]      | 30                 | Medisch onderzoek    |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het bevat_bijzondere_categorien "true"
    And is het afwijzing_reden "Bijzondere categorieën persoonsgegevens vereisen uitdrukkelijke toestemming of specifieke uitzondering conform artikel 9 AVG"

  # Automatische weigering - Ongeldige rechtsgrondslag
  Scenario: Gegevensdeling geweigerd wegens ontbrekende rechtsgrondslag
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking |
      | REQ-001     | ONGELDIG             | Marketing       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories        | aantal_betrokkenen | doel_omschrijving |
      | REQ-001     | ["NAAM", "EMAIL"]      | 100                | Marketing         |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het afwijzing_reden "Geen geldige rechtsgrondslag conform artikel 6.1 AVG voor de voorgestelde gegevensdeling"

  # Menselijke beoordeling - Gerechtvaardigd belang
  Scenario: Menselijke beoordeling vereist voor belangenafweging
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking           | gerechtvaardigd_belang_details |
      | REQ-001     | GERECHTVAARDIGD_BELANG | Fraudepreventie en risico | Bescherming bedrijfsbelangen   |
    And de volgende data categorieën:
      | aanvraag_id | data_categories           | aantal_betrokkenen | doel_omschrijving        |
      | REQ-001     | ["NAAM", "TRANSACTIES"]   | 85                 | Fraudedetectie analyse   |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het menselijke_beoordeling_nodig "true"
    And is het automatisch_toegestaan "false"
    And is het automatisch_geweigerd "false"
    And controle vereist_belangenafweging is niet leeg
    And controle vereist_belangenafweging bevat "Belangenafweging uitvoeren"

  # Menselijke beoordeling - Grote groep betrokkenen
  Scenario: Proportionaliteitstoets vereist bij groot aantal betrokkenen
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking |
      | REQ-001     | WETTELIJKE_VERPLICHTING| Statistiek      |
    And de volgende data categorieën:
      | aanvraag_id | data_categories        | aantal_betrokkenen | doel_omschrijving      |
      | REQ-001     | ["NAAM", "LEEFTIJD"]   | 5000               | Demografisch onderzoek |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het menselijke_beoordeling_nodig "true"
    And controle vereist_proportionaliteitstoets is niet leeg
    And controle vereist_proportionaliteitstoets bevat "Proportionaliteitstoets uitvoeren"

  # Menselijke beoordeling - Bijzondere categorieën met toestemming
  Scenario: Beoordeling vereist voor bijzondere categorieën met toestemming
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking         | toestemming_aanwezig |
      | REQ-001     | TOESTEMMING          | Wetenschappelijk onderzoek| true                |
    And de volgende data categorieën:
      | aanvraag_id | data_categories                    | aantal_betrokkenen | doel_omschrijving    |
      | REQ-001     | ["NAAM", "GEZONDHEIDSGEGEVENS"]    | 50                 | Medisch onderzoek    |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het menselijke_beoordeling_nodig "true"
    And is het bevat_bijzondere_categorien "true"
    And controle vereist_bijzondere_categorie_beoordeling is niet leeg
    And controle vereist_bijzondere_categorie_beoordeling bevat "Bijzondere categorie"

  # Complex scenario - Meerdere beoordelingen vereist
  Scenario: Meerdere menselijke beoordelingen vereist
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking           | gerechtvaardigd_belang_details |
      | REQ-001     | GERECHTVAARDIGD_BELANG | Risicomanagement          | Bedrijfsvoering optimalisatie  |
    And de volgende data categorieën:
      | aanvraag_id | data_categories           | aantal_betrokkenen | doel_omschrijving |
      | REQ-001     | ["NAAM", "FINANCIELE_DATA"] | 150               | Kredietbeoordeling |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het menselijke_beoordeling_nodig "true"
    And controle vereist_belangenafweging is niet leeg
    And controle vereist_proportionaliteitstoets is niet leeg

  # Edge case - Grenswaarde aantal betrokkenen
  Scenario: Precies 100 betrokkenen - automatische goedkeuring
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking |
      | REQ-001     | WETTELIJKE_VERPLICHTING| Belasting       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories        | aantal_betrokkenen | doel_omschrijving |
      | REQ-001     | ["NAAM", "BSN"]        | 100                | Belastingcontrole |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_toegestaan "true"
    And is het menselijke_beoordeling_nodig "false"

  # Edge case - 101 betrokkenen vereist beoordeling
  Scenario: Meer dan 100 betrokkenen vereist proportionaliteitstoets
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type   | doel_verwerking |
      | REQ-001     | WETTELIJKE_VERPLICHTING| Belasting       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories        | aantal_betrokkenen | doel_omschrijving |
      | REQ-001     | ["NAAM", "BSN"]        | 101                | Belastingcontrole |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het menselijke_beoordeling_nodig "true"
    And controle vereist_proportionaliteitstoets is niet leeg

  # Edge case - Alleen toegangscontroles ontbreken
  Scenario: Gegevensdeling geweigerd wegens ontbrekende toegangscontroles
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking |
      | REQ-001     | OPENBARE_TAAK        | Onderzoek       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories    | aantal_betrokkenen | doel_omschrijving |
      | REQ-001     | ["NAAM", "ADRES"]  | 25                 | Volksgezondheid   |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | false          | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het technische_voorwaarden_ok "false"

  # Edge case - Meerdere bijzondere categorieën
  Scenario: Automatische weigering bij meerdere bijzondere categorieën
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking |
      | REQ-001     | OPENBARE_TAAK        | Onderzoek       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories                                              | aantal_betrokkenen |
      | REQ-001     | ["NAAM", "GEZONDHEIDSGEGEVENS", "STRAFRECHTELIJKE_GEGEVENS"]| 20                 |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het bevat_bijzondere_categorien "true"

  # Test additional special categories
  Scenario: Automatische weigering bij etnische afkomst gegevens
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking |
      | REQ-001     | OPENBARE_TAAK        | Onderzoek       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories               | aantal_betrokkenen |
      | REQ-001     | ["NAAM", "ETNISCHE_AFKOMST"] | 15                 |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het bevat_bijzondere_categorien "true"

  Scenario: Automatische weigering bij religieuze overtuigingen
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking |
      | REQ-001     | OPENBARE_TAAK        | Onderzoek       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories                      | aantal_betrokkenen |
      | REQ-001     | ["NAAM", "RELIGIEUZE_OVERTUIGINGEN"] | 25                 |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het bevat_bijzondere_categorien "true"

  Scenario: Automatische weigering bij biometrische gegevens
    Given de volgende rechtsgrondslag gegevens:
      | aanvraag_id | rechtsgrondslag_type | doel_verwerking |
      | REQ-001     | OPENBARE_TAAK        | Onderzoek       |
    And de volgende data categorieën:
      | aanvraag_id | data_categories                   | aantal_betrokkenen |
      | REQ-001     | ["NAAM", "BIOMETRISCHE_GEGEVENS"] | 10                 |
    And de volgende beveiligingsmaatregelen:
      | aanvraag_id | encryption | access_controls | audit_logging | data_minimization |
      | REQ-001     | true       | true           | true          | true              |
    When de avg_gegevensdeling wordt uitgevoerd door VERWERKINGSVERANTWOORDELIJKE
    Then is het automatisch_geweigerd "true"
    And is het bevat_bijzondere_categorien "true"