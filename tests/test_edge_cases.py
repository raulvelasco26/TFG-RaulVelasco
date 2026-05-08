"""
Tests de casos límite del motor de cálculo.

No requieren el Excel de referencia: construyen engines ad-hoc con
datos sintéticos para verificar comportamientos en los bordes.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from engine_factory import build_engine


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _base_ss(**overrides):
    """Devuelve un session_state mínimo con solo capital inicial."""
    ss = {
        "fiscalidad": {
            "is_rate": 25.0, "iva_ventas": 21.0, "iva_compras": 21.0,
            "iva_inversiones": 21.0, "ss_autonomos_rate": 15.0,
            "ss_empresa_rate": 33.0, "ss_trabajador_rate": 6.5,
            "ss_tope_autonomos": 56640.0, "ss_tope_general": 56640.0,
            "irpf_bajo": 0.0, "irpf_medio": 20.0, "irpf_alto": 40.0,
        },
        "capex": {},
        "proyectos_inversion": {},
        "proyectos_trabajo": {},
        "financiacion": {
            "capital_inicial": {"importe": 10_000, "acciones": 100},
            "poliza_interes": 3.0,
        },
        "opex": {"gastos_fijos": {}},
        "empleados_data": {},
        "ingresos": {},
    }
    ss.update(overrides)
    return ss


def _run(ss):
    engine = build_engine(ss)
    return engine.generate_all_projections()


# ──────────────────────────────────────────────
# Motor vacío
# ──────────────────────────────────────────────

class TestMotorVacio:
    def test_genera_sin_datos(self):
        """El motor no explota con datos completamente vacíos."""
        results = _run(_base_ss())
        assert results["cuenta_resultados"] is not None
        assert results["flujo_tesoreria"] is not None
        assert results["balance"] is not None

    def test_balance_cuadra_vacio(self):
        """Activo = PN + Pasivo incluso sin ninguna operación."""
        results = _run(_base_ss())
        ba = results["balance"]
        for _, row in ba.iterrows():
            diff = abs(row["activo_total"] - row["pn_pasivo_total"])
            assert diff < 2, f"Balance descuadrado mes {row['mes']}: {diff:.2f}"


# ──────────────────────────────────────────────
# Subvención TPA al final del horizonte
# ──────────────────────────────────────────────

class TestSubvencionTPALimite:

    def test_tpa_mes_fin_60(self):
        """TPA con mes_fin=60: cobro en mes 61 (fuera del horizonte) → no aparece en CF."""
        ss = _base_ss(proyectos_trabajo={
            "tpa1": {
                "importe": 50_000, "anos": 5,
                "mes_inicio": 49, "mes_fin": 60,
                "subvencion": 10_000,
            }
        })
        results = _run(ss)
        ft = results["flujo_tesoreria"]
        cobros_subv = ft["cobros_subvenciones"].sum()
        assert cobros_subv == pytest.approx(0, abs=1)

    def test_tpa_mes_fin_59(self):
        """TPA con mes_fin=59: cobro en mes 60 (último mes) → sí aparece en CF."""
        ss = _base_ss(proyectos_trabajo={
            "tpa1": {
                "importe": 50_000, "anos": 5,
                "mes_inicio": 48, "mes_fin": 59,
                "subvencion": 10_000,
            }
        })
        results = _run(ss)
        ft = results["flujo_tesoreria"]
        cobros_subv = ft["cobros_subvenciones"].sum()
        assert cobros_subv == pytest.approx(10_000, abs=1)

    def test_tpa_mes_fin_12_cobra_en_ano2(self):
        """TPA con mes_fin=12: cobro en mes 13, que pertenece al Año 2."""
        ss = _base_ss(proyectos_trabajo={
            "tpa1": {
                "importe": 60_000, "anos": 5,
                "mes_inicio": 1, "mes_fin": 12,
                "subvencion": 20_000,
            }
        })
        results = _run(ss)
        ft = results["flujo_tesoreria"].copy()
        ft["ano"] = ((ft["mes"] - 1) // 12) + 1
        cobros_ano1 = ft[ft["ano"] == 1]["cobros_subvenciones"].sum()
        cobros_ano2 = ft[ft["ano"] == 2]["cobros_subvenciones"].sum()
        assert cobros_ano1 == pytest.approx(0, abs=1)
        assert cobros_ano2 == pytest.approx(20_000, abs=1)


# ──────────────────────────────────────────────
# Amortización de inversiones adicionales
# ──────────────────────────────────────────────

class TestInversionLimite:

    def test_inversion_mes_59_amortiza_solo_un_mes(self):
        """Inversión en mes 59: amortiza solo el mes 60 (1 mes dentro del horizonte)."""
        ss = _base_ss(proyectos_inversion={
            "pi1": {
                "importe": 12_000, "anos": 5,
                "mes_adquisicion": 59, "subvencion": 0,
            }
        })
        results = _run(ss)
        cr = results["cuenta_resultados"]
        # 12.000 / (5*12) = 200 €/mes; solo 1 mes en el horizonte
        amort_total = cr["amortizaciones"].sum()
        assert amort_total == pytest.approx(200, abs=1)

    def test_inversion_mes_1_amortiza_desde_mes_1(self):
        """Inversión en mes 1 (CAPEX inicial): amortiza desde mes 1, meses 1..13 = 13 meses."""
        ss = _base_ss(proyectos_inversion={
            "pi1": {
                "importe": 12_000, "anos": 1,
                "mes_adquisicion": 1, "subvencion": 0,
            }
        })
        results = _run(ss)
        cr = results["cuenta_resultados"]
        # amort_mensual = 12000/12 = 1000/mes
        # mes_fin_amortizacion = 1*12 + 1 = 13 → meses 1..13 = 13 meses × 1000 = 13.000
        amort_total = cr["amortizaciones"].sum()
        assert amort_total == pytest.approx(13_000, abs=1)

    def test_inversion_mes_adquisicion_mayor1_no_amortiza_en_mes_adquisicion(self):
        """Inversión adicional (mes_adq=13): el mes de adquisición NO amortiza, el siguiente sí."""
        ss = _base_ss(proyectos_inversion={
            "pi1": {
                "importe": 12_000, "anos": 5,
                "mes_adquisicion": 13, "subvencion": 0,
            }
        })
        results = _run(ss)
        cr = results["cuenta_resultados"]
        # Mes 13: adquisición → no amortiza; mes 14: primera amortización
        amort_mes13 = cr[cr["mes"] == 13]["amortizaciones"].iloc[0]
        amort_mes14 = cr[cr["mes"] == 14]["amortizaciones"].iloc[0]
        assert amort_mes13 == pytest.approx(0, abs=1)
        assert amort_mes14 == pytest.approx(12_000 / (5 * 12), abs=1)


# ──────────────────────────────────────────────
# Umbrales IRPF
# ──────────────────────────────────────────────

class TestUmbralesIRPF:

    def _engine_con_empleado(self, salario):
        ss = _base_ss(empleados_data={
            1: {
                "incremento_salario": 0.0,
                "perfiles": {
                    "perfil_a": {"num": 1, "alta": 1, "baja": 60, "salario": salario},
                },
            }
        })
        return build_engine(ss)

    def test_irpf_tramo_bajo(self):
        """Salario < 15.000 → IRPF al tramo bajo (0% por defecto)."""
        engine = self._engine_con_empleado(12_000)
        costes = engine.empleados[0].calcular_costes(engine.tax_config)
        assert costes["irpf"] == pytest.approx(0, abs=1)

    def test_irpf_tramo_medio(self):
        """15.000 ≤ salario < 90.000 → IRPF al tramo medio (20% por defecto)."""
        engine = self._engine_con_empleado(30_000)
        costes = engine.empleados[0].calcular_costes(engine.tax_config)
        assert costes["irpf"] == pytest.approx(30_000 * 0.20, abs=1)

    def test_irpf_tramo_alto(self):
        """Salario ≥ 90.000 → IRPF al tramo alto (40% por defecto)."""
        engine = self._engine_con_empleado(100_000)
        costes = engine.empleados[0].calcular_costes(engine.tax_config)
        assert costes["irpf"] == pytest.approx(100_000 * 0.40, abs=1)


# ──────────────────────────────────────────────
# Préstamos
# ──────────────────────────────────────────────

class TestPrestamosEdge:

    def test_prestamo_sin_interes(self):
        """Préstamo al 0%: total devuelto = importe del préstamo."""
        ss = _base_ss(financiacion={
            "capital_inicial": {"importe": 10_000, "acciones": 100},
            "poliza_interes": 0.0,
            "prestamo1": {
                "importe": 12_000, "mes_inicio": 1,
                "meses_carencia": 0, "meses_amortizacion": 12,
                "interes": 0.0,
            },
        })
        results = _run(ss)
        ft = results["flujo_tesoreria"]
        devolucion = ft["pagos_prestamos"].sum()
        assert devolucion == pytest.approx(12_000, abs=2)

    def test_prestamo_con_carencia(self):
        """Durante carencia solo se pagan intereses, no capital."""
        from components.financial_engine import Prestamo
        p = Prestamo(
            nombre="Test", importe=10_000, mes_inicio=1,
            meses_carencia=3, meses_amortizacion=12, interes_anual=0.06,
        )
        # Meses relativos 1,2,3 son carencia
        for mes_rel in [1, 2, 3]:
            cuota = p.get_cuota_mensual(1 + mes_rel)
            assert cuota["capital"] == pytest.approx(0, abs=0.01)
            assert cuota["intereses"] > 0
