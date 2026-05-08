"""
Fixtures compartidos para la batería de tests.

El fixture `golden_results` lee el Excel de referencia (tests/fixtures/pef_test.xlsx),
extrae los inputs con read_template y los pasa por el motor de cálculo.
Los tests comprueban que el motor produce los mismos números que el Excel.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

FIXTURE_EXCEL = os.path.join(os.path.dirname(__file__), "fixtures", "pef_test.xlsx")


@pytest.fixture(scope="session")
def golden_results():
    """Carga el Excel de referencia, ejecuta el motor y devuelve resúmenes anuales."""
    from components.excel_generator import read_template
    from engine_factory import build_engine

    with open(FIXTURE_EXCEL, "rb") as f:
        excel_bytes = f.read()

    ss = read_template(excel_bytes)
    engine = build_engine(ss)
    results = engine.generate_all_projections()

    cr = results["cuenta_resultados"].copy()
    ft = results["flujo_tesoreria"].copy()
    ba = results["balance"].copy()

    # Añadir columna 'ano' derivada de 'mes' (no hay ñ para evitar problemas de encoding)
    for df in (cr, ft, ba):
        df["ano"] = ((df["mes"] - 1) // 12) + 1

    def anual(df, col):
        return df.groupby("ano")[col].sum().to_dict()

    def anual_last(df, col):
        return df.groupby("ano")[col].last().to_dict()

    return {
        # Cuenta de Resultados  (nombres reales de columnas del motor)
        "ingresos":             anual(cr, "ingresos"),
        "costes_variables":     anual(cr, "costes_variables"),
        "margen_comercial":     anual(cr, "margen_comercial"),
        "gastos_nomina":        anual(cr, "gastos_nomina"),
        "gastos_fijos":         anual(cr, "gastos_fijos_servicios"),
        "ebitda":               anual(cr, "ebitda"),
        "amortizaciones":       anual(cr, "amortizaciones"),
        "imputacion_subv":      anual(cr, "imputacion_subvenciones"),
        "ebit":                 anual(cr, "ebit"),
        "gastos_financieros":   anual(cr, "gastos_financieros"),
        "ebt":                  anual(cr, "ebt"),
        "impuesto_sociedades":  anual(cr, "impuesto_sociedades"),
        "resultado":            anual(cr, "resultado"),
        # Flujo de Tesorería
        "cf_operaciones":       anual(ft, "cf_operaciones"),
        "cf_inversiones":       anual(ft, "cf_inversiones"),
        "cf_financiacion":      anual(ft, "cf_financiacion"),
        "cf_neto":              anual(ft, "cf_neto"),
        "cobros_subvenciones":  anual(ft, "cobros_subvenciones"),
        "cf_acumulado":         anual_last(ft, "cf_acumulado"),
        # Balance (fin de período)
        "activo_no_corriente":  anual_last(ba, "activo_no_corriente"),
        "activo_corriente":     anual_last(ba, "activo_corriente"),
        "activo_total":         anual_last(ba, "activo_total"),
        "patrimonio_neto":      anual_last(ba, "patrimonio_neto"),
        "pasivo_no_corriente":  anual_last(ba, "pasivo_no_corriente"),
        "pasivo_corriente":     anual_last(ba, "pasivo_corriente"),
        "pn_pasivo_total":      anual_last(ba, "pn_pasivo_total"),
    }
