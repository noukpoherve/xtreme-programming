import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from hubeau_client import HubEauSensorClient
from water_quality_service import WaterQualityService


def main():
    # Service 1 — Capteur IoT fluvial (données réelles Hub'eau — Seine, Paris)
    client = HubEauSensorClient(
        code_entite="F700000103",
        default_ph=7.4,  # valeur typique Seine (à remplacer par qualite_cours_eau API)
        default_turbidity=8.0,  # valeur typique Seine en conditions normales
    )

    # Service 2 — Analyse qualité de l'eau (seuils turbidité : warning=10, critical=50 NTU)
    quality_service = WaterQualityService(warning_threshold=10, critical_threshold=50)

    print("Récupération des données Hub'eau (Seine — F700000103)...")
    measurement = client.capture()

    print(f"\n[Mesure capteur]")
    print(f"  Station      : {measurement.sensor_id}")
    print(f"  UUID         : {measurement.uuid}")
    print(f"  Horodatage   : {measurement.timestamp}")
    print(f"  Niveau       : {measurement.level:.3f} m")
    print(f"  Débit        : {measurement.flow:.1f} m³/s")
    print(f"  pH           : {measurement.ph} (défaut — endpoint hydrometrie)")
    print(
        f"  Turbidité    : {measurement.turbidity} NTU (défaut — endpoint hydrometrie)"
    )

    result = quality_service.analyze(measurement)

    print(f"\n[Analyse qualité]")
    print(f"  Trace ID     : {result.trace_id}")
    print(f"  Statut global: {result.overall_status}")
    if result.has_alert:
        for alert in result.alerts:
            print(f"  ALERTE       : {alert.message}")
    else:
        print("  Aucune alerte")


if __name__ == "__main__":
    main()
