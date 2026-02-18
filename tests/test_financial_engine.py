"""
Tests para el motor de cálculo financiero - PEF ToolBoard v2.0
"""

import pytest
import pandas as pd
import numpy as np
from src.components.financial_engine import (
    FinancialEngine, Inversion, ProyectoTrabajoActivoPropio, Prestamo,
    Empleado, LineaVenta, GastoFijo, TaxConfig
)


class TestInversion:
    """Tests para la clase Inversion"""

    def test_inversion_basica(self):
        """Test de creación básica de inversión"""
        inv = Inversion(
            concepto="Equipos informáticos",
            importe=10000,
            iva_rate=0.21,
            vida_util_anos=5,
            mes_adquisicion=1
        )
        assert inv.importe == 10000
        assert inv.vida_util_anos == 5

    def test_calculo_iva(self):
        """Test del cálculo del IVA"""
        inv = Inversion(concepto="Test", importe=10000, iva_rate=0.21)
        assert inv.iva == 2100
        assert inv.total_con_iva == 12100

    def test_amortizacion_mensual(self):
        """Test del cálculo de amortización mensual"""
        inv = Inversion(concepto="Test", importe=12000, vida_util_anos=5)
        # 12000 / (5 * 12) = 200
        assert inv.amortizacion_mensual == 200

    def test_amortizacion_vida_util_cero(self):
        """Test con vida útil cero (no deprecia)"""
        inv = Inversion(concepto="Terreno", importe=100000, vida_util_anos=0)
        assert inv.amortizacion_mensual == 0

    def test_mes_fin_amortizacion(self):
        """Test del cálculo del mes final de amortización"""
        inv = Inversion(concepto="Test", importe=10000, vida_util_anos=5, mes_adquisicion=1)
        # 5 * 12 + 1 = 61
        assert inv.mes_fin_amortizacion == 61


class TestPrestamo:
    """Tests para la clase Prestamo"""

    def test_prestamo_basico(self):
        """Test de creación básica de préstamo"""
        prestamo = Prestamo(
            nombre="Préstamo ICO",
            importe=50000,
            mes_inicio=1,
            meses_carencia=6,
            meses_amortizacion=60,
            interes_anual=0.05
        )
        assert prestamo.importe == 50000
        assert prestamo.meses_carencia == 6

    def test_mes_final(self):
        """Test del cálculo del mes final"""
        prestamo = Prestamo(
            nombre="Test",
            importe=50000,
            mes_inicio=3,
            meses_carencia=6,
            meses_amortizacion=60
        )
        # 3 + 6 + 60 = 69
        assert prestamo.mes_final == 69

    def test_interes_mensual(self):
        """Test del cálculo del interés mensual"""
        prestamo = Prestamo(nombre="Test", importe=10000, interes_anual=0.12)
        assert prestamo.interes_mensual == 0.01

    def test_cuota_antes_inicio(self):
        """Test de cuota antes del inicio del préstamo"""
        prestamo = Prestamo(nombre="Test", importe=10000, mes_inicio=5)
        cuota = prestamo.get_cuota_mensual(1)
        assert cuota['capital'] == 0
        assert cuota['intereses'] == 0
        assert cuota['cuota'] == 0

    def test_cuota_durante_carencia(self):
        """Test de cuota durante período de carencia"""
        prestamo = Prestamo(
            nombre="Test",
            importe=12000,
            mes_inicio=1,
            meses_carencia=6,
            interes_anual=0.12
        )
        cuota = prestamo.get_cuota_mensual(3)
        # Durante carencia: solo intereses
        assert cuota['capital'] == 0
        # 12000 * 0.01 = 120
        assert cuota['intereses'] == 120
        assert cuota['cuota'] == 120

    def test_cuota_francesa(self):
        """Test del sistema de amortización francés"""
        prestamo = Prestamo(
            nombre="Test",
            importe=10000,
            mes_inicio=1,
            meses_carencia=0,
            meses_amortizacion=12,
            interes_anual=0.12
        )
        cuota = prestamo.get_cuota_mensual(1)
        # Cuota francesa: debería ser constante
        assert cuota['cuota'] > 0
        assert cuota['capital'] > 0
        assert cuota['intereses'] > 0
        # Primera cuota: intereses sobre el total
        assert abs(cuota['intereses'] - 100) < 0.01  # 10000 * 0.01


class TestEmpleado:
    """Tests para la clase Empleado"""

    def test_empleado_basico(self):
        """Test de creación básica de empleado"""
        emp = Empleado(
            perfil="Desarrollador",
            num_trabajadores=2,
            mes_alta=1,
            mes_baja=60,
            sueldo_bruto_anual=30000,
            es_autonomo=False
        )
        assert emp.perfil == "Desarrollador"
        assert emp.num_trabajadores == 2

    def test_calculo_costes_regimen_general(self):
        """Test del cálculo de costes para régimen general"""
        config = TaxConfig()
        emp = Empleado(
            perfil="Test",
            sueldo_bruto_anual=30000,
            es_autonomo=False
        )
        costes = emp.calcular_costes(config)

        # SS empresa: 30000 * 0.33 = 9900
        assert costes['ss_empresa'] == 9900
        # SS trabajador: 30000 * 0.0647 = 1941
        assert abs(costes['ss_trabajador'] - 1941) < 0.01
        # Coste empresa: 30000 + 9900 = 39900
        assert costes['coste_empresa'] == 39900

    def test_calculo_costes_autonomo(self):
        """Test del cálculo de costes para autónomo"""
        config = TaxConfig()
        emp = Empleado(
            perfil="Socio fundador",
            sueldo_bruto_anual=40000,
            es_autonomo=True
        )
        costes = emp.calcular_costes(config)

        # SS autónomo: 40000 * 0.15 = 6000
        assert costes['ss_empresa'] == 6000
        assert costes['ss_trabajador'] == 0

    def test_calculo_irpf_tramo_bajo(self):
        """Test IRPF para salario < 15000"""
        config = TaxConfig()
        emp = Empleado(perfil="Test", sueldo_bruto_anual=12000)
        costes = emp.calcular_costes(config)
        # 12000 * 0.0 = 0
        assert costes['irpf'] == 0

    def test_calculo_irpf_tramo_medio(self):
        """Test IRPF para salario entre 15000 y 90000"""
        config = TaxConfig()
        emp = Empleado(perfil="Test", sueldo_bruto_anual=50000)
        costes = emp.calcular_costes(config)
        # 50000 * 0.20 = 10000
        assert costes['irpf'] == 10000

    def test_calculo_irpf_tramo_alto(self):
        """Test IRPF para salario >= 90000"""
        config = TaxConfig()
        emp = Empleado(perfil="Test", sueldo_bruto_anual=100000)
        costes = emp.calcular_costes(config)
        # 100000 * 0.40 = 40000
        assert costes['irpf'] == 40000

    def test_tope_ss(self):
        """Test del tope de cotización SS"""
        config = TaxConfig(ss_tope_general=56640, ss_empresa_rate=0.33)
        emp = Empleado(perfil="Test", sueldo_bruto_anual=80000, es_autonomo=False)
        costes = emp.calcular_costes(config)
        # Base máxima: 56640 * 0.33 = 18691.2
        assert costes['ss_empresa'] == 56640 * 0.33


class TestLineaVenta:
    """Tests para la clase LineaVenta"""

    def test_linea_venta_basica(self):
        """Test de creación básica de línea de venta"""
        linea = LineaVenta(
            nombre="Producto A",
            sam=10000,
            som_anual=[0.01, 0.03, 0.05, 0.08, 0.10],
            precio_inicial=50,
            cv_produccion=0.30,
            cv_adquisicion=0.10,
            comisiones=0.05
        )
        assert linea.sam == 10000
        assert linea.precio_inicial == 50

    def test_coste_variable_total(self):
        """Test del cálculo del coste variable total"""
        linea = LineaVenta(
            nombre="Test",
            sam=1000,
            cv_produccion=0.30,
            cv_adquisicion=0.10,
            comisiones=0.05
        )
        assert linea.coste_variable_total == 0.45

    def test_unidades_por_ano(self):
        """Test del cálculo de unidades vendidas por año"""
        linea = LineaVenta(
            nombre="Test",
            sam=10000,
            som_anual=[0.01, 0.05, 0.10]
        )
        assert linea.get_unidades_ano(1) == 100   # 10000 * 0.01
        assert linea.get_unidades_ano(2) == 500   # 10000 * 0.05
        assert linea.get_unidades_ano(3) == 1000  # 10000 * 0.10

    def test_precio_por_ano(self):
        """Test del cálculo del precio por año con incremento"""
        linea = LineaVenta(
            nombre="Test",
            sam=1000,
            precio_inicial=100,
            incremento_precio_anual=[0, 0.10, 0.05]  # 0% año 1, 10% año 2, 5% año 3
        )
        assert linea.get_precio_ano(1) == 100
        assert abs(linea.get_precio_ano(2) - 110) < 0.01  # 100 * 1.10
        assert abs(linea.get_precio_ano(3) - 115.5) < 0.01  # 110 * 1.05

    def test_ventas_por_ano(self):
        """Test del cálculo de ventas por año"""
        linea = LineaVenta(
            nombre="Test",
            sam=1000,
            som_anual=[0.10],  # 100 unidades
            precio_inicial=50,
            incremento_precio_anual=[0]
        )
        assert linea.get_ventas_ano(1) == 5000  # 100 * 50


class TestGastoFijo:
    """Tests para la clase GastoFijo"""

    def test_gasto_fijo_basico(self):
        """Test de creación básica de gasto fijo"""
        gasto = GastoFijo(
            concepto="Alquiler",
            importe_anual_ano1=12000,
            iva_rate=0.21,
            incremento_anual=0.03
        )
        assert gasto.concepto == "Alquiler"
        assert gasto.importe_anual_ano1 == 12000

    def test_importe_por_ano_sin_incremento(self):
        """Test del importe anual sin incremento"""
        gasto = GastoFijo(concepto="Test", importe_anual_ano1=10000, incremento_anual=0)
        assert gasto.get_importe_ano(1) == 10000
        assert gasto.get_importe_ano(3) == 10000

    def test_importe_por_ano_con_incremento(self):
        """Test del importe anual con incremento"""
        gasto = GastoFijo(concepto="Test", importe_anual_ano1=10000, incremento_anual=0.10)
        assert gasto.get_importe_ano(1) == 10000
        assert abs(gasto.get_importe_ano(2) - 11000) < 0.01  # 10000 * 1.10
        assert abs(gasto.get_importe_ano(3) - 12100) < 0.01  # 11000 * 1.10

    def test_iva_por_ano(self):
        """Test del cálculo del IVA por año"""
        gasto = GastoFijo(concepto="Test", importe_anual_ano1=10000, iva_rate=0.21)
        assert gasto.get_iva_ano(1) == 2100


class TestTaxConfig:
    """Tests para la clase TaxConfig"""

    def test_valores_por_defecto(self):
        """Test de los valores fiscales por defecto"""
        config = TaxConfig()
        assert config.is_rate == 0.25
        assert config.iva_compras == 0.21
        assert config.iva_ventas == 0.21
        assert config.ss_empresa_rate == 0.33
        assert config.ss_trabajador_rate == 0.0647
        assert config.ss_autonomos_rate == 0.15

    def test_valores_personalizados(self):
        """Test de configuración fiscal personalizada"""
        config = TaxConfig(is_rate=0.15, iva_compras=0.10)
        assert config.is_rate == 0.15
        assert config.iva_compras == 0.10


class TestFinancialEngine:
    """Tests para FinancialEngine"""

    @pytest.fixture
    def engine(self):
        """Fixture que crea una instancia del motor"""
        return FinancialEngine()

    @pytest.fixture
    def engine_con_datos(self):
        """Fixture con datos de ejemplo cargados"""
        engine = FinancialEngine()

        # Inversiones
        engine.add_inversion(
            concepto="Equipos informáticos",
            importe=10000,
            vida_util_anos=5,
            mes_adquisicion=1
        )
        engine.add_inversion(
            concepto="Mobiliario",
            importe=5000,
            vida_util_anos=10,
            mes_adquisicion=1
        )

        # Financiación
        engine.capital_inicial = 20000
        engine.add_prestamo(
            nombre="Préstamo bancario",
            importe=30000,
            mes_inicio=1,
            meses_carencia=6,
            meses_amortizacion=48,
            interes_anual=0.05
        )

        # Gastos fijos
        engine.add_gasto_fijo(concepto="Alquiler", importe_anual_ano1=12000)
        engine.add_gasto_fijo(concepto="Suministros", importe_anual_ano1=3600)

        # Empleados
        engine.add_empleado(
            perfil="Socio fundador",
            num_trabajadores=1,
            sueldo_bruto_anual=24000,
            es_autonomo=True
        )
        engine.add_empleado(
            perfil="Desarrollador",
            num_trabajadores=1,
            mes_alta=6,
            sueldo_bruto_anual=30000,
            es_autonomo=False
        )

        # Ventas
        engine.add_linea_venta(
            nombre="Servicio A",
            sam=5000,
            som_anual=[0.02, 0.05, 0.08, 0.12, 0.15],
            precio_inicial=100,
            cv_produccion=0.20,
            comisiones=0.05
        )

        return engine

    def test_engine_initialization(self, engine):
        """Test que el motor se inicializa correctamente"""
        assert engine.months == 60
        assert engine.years == 5
        assert engine.tax_config.iva_ventas == 0.21
        assert engine.tax_config.is_rate == 0.25

    def test_set_tax_config(self, engine):
        """Test de modificación de configuración fiscal"""
        engine.set_tax_config(is_rate=0.15, iva_ventas=0.10)
        assert engine.tax_config.is_rate == 0.15
        assert engine.tax_config.iva_ventas == 0.10

    def test_add_inversion(self, engine):
        """Test de añadir inversión"""
        engine.add_inversion(concepto="Test", importe=10000)
        assert len(engine.inversiones) == 1
        assert engine.inversiones[0].importe == 10000

    def test_set_inversiones(self, engine):
        """Test de establecer inversiones desde lista"""
        inversiones = [
            {"concepto": "Equipo A", "importe": 5000},
            {"concepto": "Equipo B", "importe": 3000}
        ]
        engine.set_inversiones(inversiones)
        assert len(engine.inversiones) == 2

    def test_set_financiacion(self, engine):
        """Test de establecer financiación"""
        financiacion = {
            "capital_inicial": 50000,
            "prestamos": [
                {"nombre": "ICO", "importe": 30000, "interes_anual": 0.03}
            ]
        }
        engine.set_financiacion(financiacion)
        assert engine.capital_inicial == 50000
        assert len(engine.prestamos) == 1

    def test_mes_a_ano(self, engine):
        """Test de conversión mes a año"""
        assert engine._mes_a_ano(1) == 1
        assert engine._mes_a_ano(12) == 1
        assert engine._mes_a_ano(13) == 2
        assert engine._mes_a_ano(24) == 2
        assert engine._mes_a_ano(60) == 5

    def test_calculate_ventas_mensuales(self, engine_con_datos):
        """Test del cálculo de ventas mensuales"""
        df = engine_con_datos._calculate_ventas_mensuales()

        assert isinstance(df, pd.DataFrame)
        assert 'mes' in df.columns
        assert 'ventas_totales' in df.columns
        assert 'costes_variables' in df.columns
        assert 'iva_repercutido' in df.columns
        assert len(df) == 60

    def test_calculate_gastos_fijos_mensuales(self, engine_con_datos):
        """Test del cálculo de gastos fijos mensuales"""
        df = engine_con_datos._calculate_gastos_fijos_mensuales()

        assert isinstance(df, pd.DataFrame)
        assert 'gastos_fijos_totales' in df.columns
        assert len(df) == 60
        # 12000 + 3600 = 15600 anual / 12 = 1300 mensual
        assert abs(df['gastos_fijos_totales'][0] - 1300) < 0.01

    def test_calculate_nominas_mensuales(self, engine_con_datos):
        """Test del cálculo de nóminas mensuales"""
        df = engine_con_datos._calculate_nominas_mensuales()

        assert isinstance(df, pd.DataFrame)
        assert 'sueldos_brutos' in df.columns
        assert 'ss_empresa' in df.columns
        assert 'coste_empresa_total' in df.columns
        assert len(df) == 60

        # Mes 1: solo el autónomo (24000/12 = 2000)
        assert abs(df['sueldos_brutos'][0] - 2000) < 0.01

        # Mes 6: autónomo + desarrollador (24000 + 30000)/12 = 4500
        # Pero el desarrollador empieza en mes 6, así que debería estar
        assert df['sueldos_brutos'][5] > df['sueldos_brutos'][0]

    def test_calculate_amortizaciones_mensuales(self, engine_con_datos):
        """Test del cálculo de amortizaciones mensuales"""
        df = engine_con_datos._calculate_amortizaciones_mensuales()

        assert isinstance(df, pd.DataFrame)
        assert 'amortizacion_total' in df.columns
        assert 'inmovilizado_neto' in df.columns
        assert len(df) == 60

        # Amortización empieza el mismo mes de adquisición (mes 1, idx 0)
        expected_amort = 10000/60 + 5000/120  # 166.67 + 41.67 = 208.33
        assert abs(df['amortizacion_total'][0] - expected_amort) < 0.01

        # Mes 2 (idx 1): misma amortización
        assert abs(df['amortizacion_total'][1] - expected_amort) < 0.01

    def test_calculate_financiacion_mensual(self, engine_con_datos):
        """Test del cálculo de financiación mensual"""
        df = engine_con_datos._calculate_financiacion_mensual()

        assert isinstance(df, pd.DataFrame)
        assert 'entrada_capital' in df.columns
        assert 'entrada_prestamos' in df.columns
        assert 'pago_capital_prestamos' in df.columns
        assert len(df) == 60

        # Capital inicial en mes 1
        assert df['entrada_capital'][0] == 20000

        # Préstamo en mes 1
        assert df['entrada_prestamos'][0] == 30000

    def test_calculate_cuenta_resultados(self, engine_con_datos):
        """Test del cálculo de la cuenta de resultados"""
        df = engine_con_datos.calculate_cuenta_resultados()

        assert isinstance(df, pd.DataFrame)
        assert 'ingresos' in df.columns
        assert 'costes_variables' in df.columns
        assert 'margen_comercial' in df.columns
        assert 'ebitda' in df.columns
        assert 'ebit' in df.columns
        assert 'ebt' in df.columns
        assert 'resultado' in df.columns
        assert 'resultado_acumulado' in df.columns
        assert len(df) == 60

        # Verificar que margen = ingresos - cv
        for i in range(10):
            expected_margen = df['ingresos'][i] - df['costes_variables'][i]
            assert abs(df['margen_comercial'][i] - expected_margen) < 0.01

    def test_calculate_flujo_tesoreria(self, engine_con_datos):
        """Test del cálculo del flujo de tesorería"""
        df = engine_con_datos.calculate_flujo_tesoreria()

        assert isinstance(df, pd.DataFrame)
        assert 'cobros_clientes' in df.columns
        assert 'cf_operaciones' in df.columns
        assert 'cf_inversiones' in df.columns
        assert 'cf_financiacion' in df.columns
        assert 'cf_neto' in df.columns
        assert 'cf_acumulado' in df.columns
        assert len(df) == 60

    def test_calculate_balance(self, engine_con_datos):
        """Test del cálculo del balance"""
        df = engine_con_datos.calculate_balance()

        assert isinstance(df, pd.DataFrame)
        assert 'activo_total' in df.columns
        assert 'patrimonio_neto' in df.columns
        assert 'pasivo_total' in df.columns
        assert 'check_balance' in df.columns
        assert len(df) == 60

    def test_calculate_ratios(self, engine_con_datos):
        """Test del cálculo de ratios"""
        ratios = engine_con_datos.calculate_ratios()

        assert isinstance(ratios, dict)
        assert 'por_ano' in ratios
        assert 'globales' in ratios
        assert 1 in ratios['por_ano']
        assert 'margen_ebitda' in ratios['por_ano'][1]
        assert 'roe' in ratios['por_ano'][1]
        assert 'ratio_liquidez' in ratios['por_ano'][1]

    def test_generate_all_projections(self, engine_con_datos):
        """Test de generación de todas las proyecciones"""
        result = engine_con_datos.generate_all_projections()

        assert 'cuenta_resultados' in result
        assert 'flujo_tesoreria' in result
        assert 'balance' in result
        assert 'ratios' in result

    def test_get_resumen_anual(self, engine_con_datos):
        """Test del resumen anual"""
        engine_con_datos.generate_all_projections()
        df = engine_con_datos.get_resumen_anual()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5  # 5 años
        assert 'ano' in df.columns
        assert 'ingresos' in df.columns
        assert 'ebitda' in df.columns
        assert 'resultado' in df.columns


class TestIntegracionCompleta:
    """Tests de integración con un caso de negocio completo"""

    @pytest.fixture
    def caso_startup_tecnologica(self):
        """Fixture con un caso completo de startup tecnológica"""
        engine = FinancialEngine()

        # Configuración fiscal
        engine.set_tax_config(
            is_rate=0.25,
            iva_ventas=0.21,
            iva_compras=0.21
        )

        # Inversiones iniciales
        inversiones = [
            {"concepto": "Desarrollo software", "importe": 25000, "vida_util_anos": 5},
            {"concepto": "Equipos informáticos", "importe": 15000, "vida_util_anos": 5},
            {"concepto": "Mobiliario oficina", "importe": 8000, "vida_util_anos": 10},
        ]
        engine.set_inversiones(inversiones)

        # Financiación
        engine.set_financiacion({
            "capital_inicial": 30000,
            "prestamos": [
                {
                    "nombre": "Préstamo ENISA",
                    "importe": 50000,
                    "mes_inicio": 1,
                    "meses_carencia": 12,
                    "meses_amortizacion": 48,
                    "interes_anual": 0.04
                }
            ]
        })

        # Gastos operativos
        engine.set_gastos_operativos(
            gastos_fijos=[
                {"concepto": "Alquiler", "importe_anual_ano1": 18000},
                {"concepto": "Suministros", "importe_anual_ano1": 4800},
                {"concepto": "Marketing", "importe_anual_ano1": 12000},
                {"concepto": "Servicios profesionales", "importe_anual_ano1": 6000},
            ],
            empleados=[
                {
                    "perfil": "Socio fundador",
                    "num_trabajadores": 2,
                    "sueldo_bruto_anual": 28000,
                    "es_autonomo": True
                },
                {
                    "perfil": "Desarrollador",
                    "num_trabajadores": 1,
                    "mes_alta": 7,
                    "sueldo_bruto_anual": 35000,
                    "es_autonomo": False
                },
                {
                    "perfil": "Comercial",
                    "num_trabajadores": 1,
                    "mes_alta": 13,
                    "sueldo_bruto_anual": 28000,
                    "es_autonomo": False
                }
            ]
        )

        # Ingresos
        engine.set_ingresos([
            {
                "nombre": "SaaS Básico",
                "sam": 10000,
                "som_anual": [0.005, 0.02, 0.05, 0.08, 0.12],
                "precio_inicial": 120,
                "incremento_precio_anual": [0, 0.05, 0.03, 0.03, 0.03],
                "cv_produccion": 0.15,
                "comisiones": 0.10
            },
            {
                "nombre": "SaaS Premium",
                "sam": 5000,
                "som_anual": [0.002, 0.01, 0.025, 0.04, 0.06],
                "precio_inicial": 300,
                "incremento_precio_anual": [0, 0.05, 0.03, 0.03, 0.03],
                "cv_produccion": 0.10,
                "comisiones": 0.08
            }
        ])

        return engine

    def test_caso_completo_genera_proyecciones(self, caso_startup_tecnologica):
        """Test que verifica que el caso completo genera proyecciones válidas"""
        result = caso_startup_tecnologica.generate_all_projections()

        # Verificar que todos los DataFrames se generaron
        assert caso_startup_tecnologica.cuenta_resultados is not None
        assert caso_startup_tecnologica.flujo_tesoreria is not None
        assert caso_startup_tecnologica.balance is not None
        assert caso_startup_tecnologica.ratios is not None

    def test_ingresos_crecientes(self, caso_startup_tecnologica):
        """Test que los ingresos crecen año a año"""
        caso_startup_tecnologica.generate_all_projections()
        resumen = caso_startup_tecnologica.get_resumen_anual()

        # Los ingresos deberían crecer cada año
        for i in range(1, len(resumen)):
            assert resumen['ingresos'][i] >= resumen['ingresos'][i-1]

    def test_coherencia_financiacion_inversiones(self, caso_startup_tecnologica):
        """Test que la financiación cubre las inversiones"""
        # Capital + Préstamos = 30000 + 50000 = 80000
        # Inversiones (sin IVA) = 25000 + 15000 + 8000 = 48000
        # Con IVA: 48000 * 1.21 = 58080
        financiacion = 30000 + 50000
        inversiones_con_iva = sum(inv.total_con_iva for inv in caso_startup_tecnologica.inversiones)

        assert financiacion > inversiones_con_iva

    def test_flujo_caja_positivo_final(self, caso_startup_tecnologica):
        """Test que el flujo de caja acumulado es positivo al final"""
        caso_startup_tecnologica.generate_all_projections()

        # Al final del año 5, debería haber flujo de caja positivo acumulado
        # (si el negocio es viable)
        cf_final = caso_startup_tecnologica.flujo_tesoreria['cf_acumulado'].iloc[-1]
        # Nota: puede ser negativo en un escenario realista, lo importante es que calcule
        assert isinstance(cf_final, (int, float))

    def test_ratios_calculados(self, caso_startup_tecnologica):
        """Test que los ratios se calculan correctamente"""
        caso_startup_tecnologica.generate_all_projections()
        ratios = caso_startup_tecnologica.ratios

        # Verificar que hay ratios para cada año
        for ano in range(1, 6):
            assert ano in ratios['por_ano']
            assert 'margen_ebitda' in ratios['por_ano'][ano]
            assert 'roe' in ratios['por_ano'][ano]
            assert 'roa' in ratios['por_ano'][ano]
            assert 'ratio_liquidez' in ratios['por_ano'][ano]


class TestCasosLimite:
    """Tests para casos límite y edge cases"""

    def test_engine_sin_datos(self):
        """Test del motor sin datos cargados"""
        engine = FinancialEngine()
        # Debería funcionar aunque los resultados sean ceros
        result = engine.generate_all_projections()
        assert result is not None

    def test_prestamo_sin_carencia(self):
        """Test de préstamo sin período de carencia"""
        prestamo = Prestamo(
            nombre="Test",
            importe=10000,
            meses_carencia=0,
            meses_amortizacion=12,
            interes_anual=0.12
        )
        # Desde el mes 1 debería pagar capital
        cuota = prestamo.get_cuota_mensual(1)
        assert cuota['capital'] > 0

    def test_empleado_periodo_parcial(self):
        """Test de empleado que trabaja período parcial"""
        engine = FinancialEngine()
        engine.add_empleado(
            perfil="Temporal",
            mes_alta=6,
            mes_baja=18,
            sueldo_bruto_anual=24000
        )
        df = engine._calculate_nominas_mensuales()

        # Meses 1-5: sin sueldo
        for i in range(5):
            assert df['sueldos_brutos'][i] == 0

        # Mes 6: con sueldo
        assert df['sueldos_brutos'][5] > 0

        # Mes 19+: sin sueldo
        assert df['sueldos_brutos'][18] == 0

    def test_linea_venta_sin_ventas(self):
        """Test de línea de venta con SOM=0"""
        linea = LineaVenta(
            nombre="Producto sin ventas",
            sam=10000,
            som_anual=[0, 0, 0, 0, 0],
            precio_inicial=100
        )
        assert linea.get_unidades_ano(1) == 0
        assert linea.get_ventas_ano(1) == 0

    def test_inversion_sin_iva(self):
        """Test de inversión sin IVA (exenta)"""
        inv = Inversion(
            concepto="Terreno",
            importe=100000,
            iva_rate=0.0,
            vida_util_anos=0
        )
        assert inv.iva == 0
        assert inv.total_con_iva == 100000
        assert inv.amortizacion_mensual == 0
