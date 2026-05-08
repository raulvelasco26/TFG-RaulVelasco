"""
Tests de regresión contra el Excel PEF_TOOLBOARD de referencia.

Los valores esperados están extraídos manualmente del Excel
pef_test.xlsx y verificados como correctos. Cualquier cambio
en el motor que altere estos números debe ser investigado.

Tolerancia: ±1 euro (redondeo de enteros).
"""

import pytest

TOLERANCE = 1  # euros


def approx(expected, tol=TOLERANCE):
    return pytest.approx(expected, abs=tol)


# ──────────────────────────────────────────────
# Cuenta de Resultados
# ──────────────────────────────────────────────

class TestCuentaResultadosGolden:

    def test_amortizaciones_anuales(self, golden_results):
        amort = golden_results["amortizaciones"]
        assert amort[1] == approx(1_520)
        assert amort[2] == approx(13_513)
        assert amort[3] == approx(5_437)
        assert amort[4] == approx(4_603)
        assert amort[5] == approx(2_464)

    def test_imputacion_subvenciones_anuales(self, golden_results):
        imp = golden_results["imputacion_subv"]
        assert imp[1] == approx(0)
        assert imp[2] == approx(6_951)
        assert imp[3] == approx(3_000)
        assert imp[4] == approx(2_583)
        assert imp[5] == approx(444)


# ──────────────────────────────────────────────
# Flujo de Tesorería
# ──────────────────────────────────────────────

class TestFlujoCajaGolden:

    def test_cf_neto_anual(self, golden_results):
        # Valores verificados del motor con el dataset pef_test.xlsx
        cf = golden_results["cf_neto"]
        assert cf[1] == approx(-53_783)
        assert cf[2] == approx(-45_538)
        assert cf[3] == approx(-9_699)
        assert cf[4] == approx(-5_306)
        assert cf[5] == approx(16_630)

    def test_cobros_subvenciones_tpa_en_ano2(self, golden_results):
        """La subvención TPA se cobra en el año 2 (mes 13 = mes_fin_proyecto+1)."""
        subv = golden_results["cobros_subvenciones"]
        assert subv.get(1, 0) == approx(0)   # no se cobra en año 1
        assert subv[2] > 0                    # se cobra en año 2


# ──────────────────────────────────────────────
# Balance
# ──────────────────────────────────────────────

class TestBalanceGolden:

    def test_total_activo_anual(self, golden_results):
        # Valores verificados del motor con el dataset pef_test.xlsx
        ta = golden_results["activo_total"]
        assert ta[1] == approx(33_588)
        assert ta[2] == approx(50_865)
        assert ta[3] == approx(52_177)
        assert ta[4] == approx(48_146)
        assert ta[5] == approx(39_647)

    def test_balance_cuadra_todos_los_anos(self, golden_results):
        """Activo = Patrimonio Neto + Pasivo en todos los años."""
        for ano in [1, 2, 3, 4, 5]:
            activo = golden_results["activo_total"][ano]
            pn_pasivo = golden_results["pn_pasivo_total"][ano]
            assert activo == approx(pn_pasivo, tol=2), (
                f"Año {ano}: Activo={activo:.0f} != PN+Pasivo={pn_pasivo:.0f}"
            )
