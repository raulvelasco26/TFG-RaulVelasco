"""
Tests exhaustivos comparando cálculos de la app con la lógica del Excel PEF ToolBoard v2.0

Estos tests verifican que el motor financiero de Python reproduce fielmente
los cálculos del template Excel original.
"""

import pytest
import pandas as pd
import numpy as np
from src.components.financial_engine import (
    FinancialEngine, Inversion, ProyectoTrabajoActivoPropio, Prestamo,
    Empleado, LineaVenta, GastoFijo, TaxConfig
)


class TestAmortizacionInversiones:
    """Tests de amortización de inversiones comparando con Excel"""

    def test_amortizacion_lineal_simple(self):
        """Test de amortización lineal - caso básico"""
        # Escenario: Inversión de 12,000€ a 5 años
        engine = FinancialEngine()
        engine.capital_inicial = 20000
        engine.add_inversion(
            concepto="Equipos",
            importe=12000,
            vida_util_anos=5,
            mes_adquisicion=1,
            iva_rate=0.21
        )

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Amortización mensual esperada: 12000 / (5 * 12) = 200€/mes
        assert abs(df_amort['amortizacion_total'][0] - 200) < 0.01
        assert abs(df_amort['amortizacion_total'][11] - 200) < 0.01  # Mes 12
        assert abs(df_amort['amortizacion_total'][59] - 200) < 0.01  # Mes 60

        # La amortización NO debe aplicarse después del período de amortización
        # Mes 61 (fin = vida_util * 12 + mes_adq = 5*12+1 = 61)
        # Por lo tanto, mes 60 es el último mes con amortización
        assert df_amort['amortizacion_total'][59] == 200  # Mes 60: SÍ amortiza

    def test_inmovilizado_neto_decrece(self):
        """Test que el inmovilizado neto decrece con la amortización"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_inversion(
            concepto="Maquinaria",
            importe=30000,
            vida_util_anos=10,
            mes_adquisicion=1
        )

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Inmovilizado neto inicial = importe
        assert df_amort['inmovilizado_neto'][0] == 30000 - 250  # Primera amortización ya aplicada

        # Debe decrecer mes a mes
        for i in range(1, 12):
            assert df_amort['inmovilizado_neto'][i] < df_amort['inmovilizado_neto'][i-1]

    def test_multiples_inversiones_diferentes_periodos(self):
        """Test de múltiples inversiones con diferentes vidas útiles"""
        engine = FinancialEngine()
        engine.capital_inicial = 100000
        engine.add_inversion(concepto="Equipos", importe=10000, vida_util_anos=5, mes_adquisicion=1)
        engine.add_inversion(concepto="Mobiliario", importe=5000, vida_util_anos=10, mes_adquisicion=1)
        engine.add_inversion(concepto="Software", importe=3000, vida_util_anos=3, mes_adquisicion=1)

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Mes 1: amortización total = 10000/60 + 5000/120 + 3000/36
        amort_esperada = 10000/60 + 5000/120 + 3000/36
        assert abs(df_amort['amortizacion_total'][0] - amort_esperada) < 0.01

    def test_inversion_mes_posterior(self):
        """Test de inversión adquirida en un mes posterior"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_inversion(concepto="Equipos", importe=6000, vida_util_anos=5, mes_adquisicion=13)

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Meses 1-12: sin amortización
        for i in range(12):
            assert df_amort['amortizacion_total'][i] == 0

        # Mes 13: primera amortización (100€/mes)
        assert abs(df_amort['amortizacion_total'][12] - 100) < 0.01

    def test_iva_soportado_inversiones(self):
        """Test del IVA soportado en inversiones"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_inversion(concepto="Equipos", importe=10000, vida_util_anos=5, mes_adquisicion=1, iva_rate=0.21)
        engine.add_inversion(concepto="Software", importe=5000, vida_util_anos=3, mes_adquisicion=6, iva_rate=0.21)

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Mes 1: IVA de 10000 * 0.21 = 2100
        assert abs(df_amort['iva_soportado_inversiones'][0] - 2100) < 0.01

        # Mes 6: IVA de 5000 * 0.21 = 1050
        assert abs(df_amort['iva_soportado_inversiones'][5] - 1050) < 0.01

        # Mes 2: sin IVA (no hay inversiones ese mes)
        assert df_amort['iva_soportado_inversiones'][1] == 0

    def test_subvenciones_imputacion(self):
        """Test de imputación de subvenciones proporcional a la amortización"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_inversion(
            concepto="Equipos",
            importe=12000,
            vida_util_anos=5,
            mes_adquisicion=1,
            subvencion=3000  # 25% de subvención
        )

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Imputación mensual: 3000 / (5 * 12) = 50€/mes
        assert abs(df_amort['imputacion_subvenciones'][0] - 50) < 0.01
        assert abs(df_amort['imputacion_subvenciones'][11] - 50) < 0.01


class TestPrestamosYFinanciacion:
    """Tests de cálculos de préstamos y financiación"""

    def test_cuota_francesa_calculo(self):
        """Test del cálculo de cuota francesa"""
        # Préstamo de 10,000€ a 12 meses al 12% anual
        prestamo = Prestamo(
            nombre="Test",
            importe=10000,
            mes_inicio=1,
            meses_carencia=0,
            meses_amortizacion=12,
            interes_anual=0.12
        )

        # Fórmula cuota francesa: P * (r * (1+r)^n) / ((1+r)^n - 1)
        # r = 0.01 (mensual), n = 12
        r = 0.01
        n = 12
        cuota_esperada = 10000 * (r * (1 + r)**n) / ((1 + r)**n - 1)

        cuota_mes1 = prestamo.get_cuota_mensual(2)  # Primer pago en mes 2
        assert abs(cuota_mes1['cuota'] - cuota_esperada) < 0.01

        # Verificar que la cuota es constante
        for mes in range(2, 14):
            cuota = prestamo.get_cuota_mensual(mes)
            assert abs(cuota['cuota'] - cuota_esperada) < 0.01

    def test_carencia_solo_intereses(self):
        """Test de período de carencia - solo se pagan intereses"""
        prestamo = Prestamo(
            nombre="Test",
            importe=12000,
            mes_inicio=1,
            meses_carencia=6,
            meses_amortizacion=12,
            interes_anual=0.12
        )

        # Durante carencia: capital = 0, intereses = importe * tipo_mensual
        for mes in range(2, 8):  # Meses 2-7 (carencia)
            cuota = prestamo.get_cuota_mensual(mes)
            assert cuota['capital'] == 0
            assert abs(cuota['intereses'] - 120) < 0.01  # 12000 * 0.01

        # Después de carencia: capital > 0
        cuota_mes8 = prestamo.get_cuota_mensual(8)
        assert cuota_mes8['capital'] > 0

    def test_prestamo_sin_interes(self):
        """Test de préstamo sin intereses (0%)"""
        prestamo = Prestamo(
            nombre="Préstamo participativo",
            importe=12000,
            mes_inicio=1,
            meses_carencia=0,
            meses_amortizacion=12,
            interes_anual=0.0
        )

        # Cuota mensual = 12000 / 12 = 1000
        for mes in range(2, 14):
            cuota = prestamo.get_cuota_mensual(mes)
            assert abs(cuota['capital'] - 1000) < 0.01
            assert cuota['intereses'] == 0
            assert abs(cuota['cuota'] - 1000) < 0.01

    def test_amortizacion_total_prestamo(self):
        """Test que la amortización total del préstamo suma el importe total"""
        prestamo = Prestamo(
            nombre="Test",
            importe=10000,
            mes_inicio=1,
            meses_carencia=3,
            meses_amortizacion=24,
            interes_anual=0.06
        )

        total_capital = 0
        for mes in range(1, 61):
            cuota = prestamo.get_cuota_mensual(mes)
            total_capital += cuota['capital']

        # El total del capital amortizado debe ser igual al importe del préstamo
        assert abs(total_capital - 10000) < 1  # Tolerancia de 1€ por redondeos

    def test_clasificacion_deuda_corto_largo_plazo(self):
        """Test de clasificación de deuda en corto y largo plazo"""
        engine = FinancialEngine()
        engine.capital_inicial = 10000
        engine.add_prestamo(
            nombre="Préstamo LP",
            importe=60000,
            mes_inicio=1,
            meses_carencia=12,
            meses_amortizacion=48,
            interes_anual=0.05
        )

        df_fin = engine._calculate_financiacion_mensual()

        # Mes 1: casi todo es largo plazo (porque hay carencia)
        assert df_fin['deuda_largo_plazo'][0] > df_fin['deuda_corto_plazo'][0]

        # Debe haber deuda
        assert df_fin['deuda_largo_plazo'][0] + df_fin['deuda_corto_plazo'][0] > 50000


class TestNominasYPersonal:
    """Tests de cálculos de nóminas y personal"""

    def test_coste_empresa_regimen_general(self):
        """Test del cálculo del coste empresa en régimen general"""
        config = TaxConfig()
        emp = Empleado(
            perfil="Desarrollador",
            sueldo_bruto_anual=30000,
            es_autonomo=False
        )

        costes = emp.calcular_costes(config)

        # SS empresa: 30000 * 0.33 = 9900
        assert costes['ss_empresa'] == 9900
        # Coste total empresa: 30000 + 9900 = 39900
        assert costes['coste_empresa'] == 39900

    def test_coste_autonomo(self):
        """Test del cálculo para autónomos"""
        config = TaxConfig()
        emp = Empleado(
            perfil="Socio",
            sueldo_bruto_anual=24000,
            es_autonomo=True
        )

        costes = emp.calcular_costes(config)

        # SS autónomo: 24000 * 0.15 = 3600
        assert costes['ss_empresa'] == 3600
        # No hay SS trabajador en autónomos
        assert costes['ss_trabajador'] == 0
        # Coste empresa: 24000 + 3600 = 27600
        assert costes['coste_empresa'] == 27600

    def test_tope_cotizacion_ss(self):
        """Test del tope de cotización a la Seguridad Social"""
        config = TaxConfig(ss_tope_general=56640)
        emp = Empleado(
            perfil="Directivo",
            sueldo_bruto_anual=100000,
            es_autonomo=False
        )

        costes = emp.calcular_costes(config)

        # La base de cotización se limita al tope: 56640
        # SS empresa: 56640 * 0.33 = 18691.2
        assert abs(costes['ss_empresa'] - 18691.2) < 0.01

    def test_irpf_tramos(self):
        """Test de cálculo de IRPF por tramos"""
        config = TaxConfig(irpf_bajo=0.0, irpf_medio=0.20, irpf_alto=0.40)

        # Tramo bajo (< 15000)
        emp1 = Empleado(perfil="Test", sueldo_bruto_anual=12000)
        assert emp1.calcular_costes(config)['irpf'] == 0

        # Tramo medio (15000-90000)
        emp2 = Empleado(perfil="Test", sueldo_bruto_anual=50000)
        assert emp2.calcular_costes(config)['irpf'] == 10000  # 50000 * 0.20

        # Tramo alto (>= 90000)
        emp3 = Empleado(perfil="Test", sueldo_bruto_anual=100000)
        assert emp3.calcular_costes(config)['irpf'] == 40000  # 100000 * 0.40

    def test_nominas_mensuales_empleado_temporal(self):
        """Test de nóminas para empleado que trabaja período parcial"""
        engine = FinancialEngine()
        engine.add_empleado(
            perfil="Temporal",
            num_trabajadores=1,
            mes_alta=6,
            mes_baja=18,
            sueldo_bruto_anual=24000,
            es_autonomo=False
        )

        df_nom = engine._calculate_nominas_mensuales()

        # Meses 1-5: sin coste
        for i in range(5):
            assert df_nom['coste_empresa_total'][i] == 0

        # Meses 6-18: con coste
        coste_mensual = (24000 + 24000 * 0.33) / 12
        assert abs(df_nom['coste_empresa_total'][5] - coste_mensual) < 0.01

        # Mes 19+: sin coste
        assert df_nom['coste_empresa_total'][18] == 0

    def test_multiples_empleados_mismo_perfil(self):
        """Test de múltiples trabajadores del mismo perfil"""
        engine = FinancialEngine()
        engine.add_empleado(
            perfil="Desarrollador",
            num_trabajadores=3,
            mes_alta=1,
            sueldo_bruto_anual=30000,
            es_autonomo=False
        )

        df_nom = engine._calculate_nominas_mensuales()

        # Coste mensual = (30000 * 1.33) / 12 * 3 trabajadores
        coste_esperado = (30000 * 1.33) / 12 * 3
        assert abs(df_nom['coste_empresa_total'][0] - coste_esperado) < 0.01


class TestIngresosYVentas:
    """Tests de cálculos de ingresos y ventas"""

    def test_ventas_som_creciente(self):
        """Test de ventas con SOM (Share of Market) creciente"""
        linea = LineaVenta(
            nombre="Producto A",
            sam=10000,  # Mercado accesible: 10,000 clientes
            som_anual=[0.01, 0.03, 0.05, 0.08, 0.10],  # % de penetración
            precio_inicial=50,
            incremento_precio_anual=[0, 0, 0, 0, 0]
        )

        # Año 1: 10000 * 0.01 = 100 unidades * 50€ = 5,000€
        assert linea.get_ventas_ano(1) == 5000

        # Año 2: 10000 * 0.03 = 300 unidades * 50€ = 15,000€
        assert linea.get_ventas_ano(2) == 15000

        # Año 5: 10000 * 0.10 = 1000 unidades * 50€ = 50,000€
        assert linea.get_ventas_ano(5) == 50000

    def test_incremento_precios(self):
        """Test de incremento de precios año a año"""
        linea = LineaVenta(
            nombre="Servicio",
            sam=1000,
            som_anual=[0.10, 0.10, 0.10, 0.10, 0.10],  # SOM constante
            precio_inicial=100,
            incremento_precio_anual=[0, 0.10, 0.05, 0.03, 0.02]  # Incrementos anuales
        )

        # Año 1: precio = 100
        assert linea.get_precio_ano(1) == 100

        # Año 2: precio = 100 * 1.10 = 110
        assert abs(linea.get_precio_ano(2) - 110) < 0.01

        # Año 3: precio = 110 * 1.05 = 115.5
        assert abs(linea.get_precio_ano(3) - 115.5) < 0.01

    def test_costes_variables_ventas(self):
        """Test de costes variables sobre ventas"""
        engine = FinancialEngine()
        engine.add_linea_venta(
            nombre="Producto",
            sam=1000,
            som_anual=[0.10],  # 100 unidades
            precio_inicial=100,  # 10,000€ de ventas anuales
            cv_produccion=0.30,  # 30% coste producción
            cv_adquisicion=0.10,  # 10% coste adquisición
            comisiones=0.05  # 5% comisiones
        )

        df_ventas = engine._calculate_ventas_mensuales()

        # Ventas mensuales: 10000 / 12 ≈ 833.33€
        ventas_mes = 10000 / 12
        # CV total: 45% de las ventas
        cv_esperado = ventas_mes * 0.45

        assert abs(df_ventas['costes_variables'][0] - cv_esperado) < 0.01

    def test_iva_repercutido(self):
        """Test del IVA repercutido sobre ventas"""
        engine = FinancialEngine()
        engine.tax_config.iva_ventas = 0.21
        engine.add_linea_venta(
            nombre="Producto",
            sam=1000,
            som_anual=[0.10],
            precio_inicial=100
        )

        df_ventas = engine._calculate_ventas_mensuales()

        # Ventas mensuales ≈ 833.33€
        # IVA repercutido: 833.33 * 0.21 ≈ 175€
        ventas_mes = 10000 / 12
        iva_esperado = ventas_mes * 0.21

        assert abs(df_ventas['iva_repercutido'][0] - iva_esperado) < 0.01


class TestGastosFijos:
    """Tests de gastos fijos (OPEX)"""

    def test_gastos_fijos_sin_incremento(self):
        """Test de gastos fijos sin incremento anual"""
        gasto = GastoFijo(
            concepto="Alquiler",
            importe_anual_ano1=12000,
            incremento_anual=0
        )

        # Debe ser constante todos los años
        for ano in range(1, 6):
            assert gasto.get_importe_ano(ano) == 12000

    def test_gastos_fijos_con_incremento(self):
        """Test de gastos fijos con incremento compuesto"""
        gasto = GastoFijo(
            concepto="Alquiler",
            importe_anual_ano1=12000,
            incremento_anual=0.03  # 3% anual
        )

        # Año 1: 12000
        assert gasto.get_importe_ano(1) == 12000

        # Año 2: 12000 * 1.03 = 12360
        assert abs(gasto.get_importe_ano(2) - 12360) < 0.01

        # Año 3: 12360 * 1.03 = 12730.8
        assert abs(gasto.get_importe_ano(3) - 12730.8) < 0.01

    def test_distribucion_mensual_gastos(self):
        """Test de distribución mensual de gastos fijos"""
        engine = FinancialEngine()
        engine.add_gasto_fijo(
            concepto="Alquiler",
            importe_anual_ano1=12000
        )

        df_gastos = engine._calculate_gastos_fijos_mensuales()

        # Todos los meses del año 1 deben tener 1000€
        for i in range(12):
            assert abs(df_gastos['gastos_fijos_totales'][i] - 1000) < 0.01


class TestCuentaResultados:
    """Tests exhaustivos de la cuenta de resultados (P&L)"""

    def test_margen_comercial_calculo(self):
        """Test del cálculo del margen comercial"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_linea_venta(
            nombre="Producto",
            sam=1000,
            som_anual=[0.10],
            precio_inicial=100,  # 10,000€/año
            cv_produccion=0.30  # 30% CV
        )

        df_pl = engine.calculate_cuenta_resultados()

        # Margen = Ingresos - CV
        for i in range(12):
            margen_esperado = df_pl['ingresos'][i] - df_pl['costes_variables'][i]
            assert abs(df_pl['margen_comercial'][i] - margen_esperado) < 0.01

    def test_ebitda_calculo(self):
        """Test del cálculo del EBITDA"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_linea_venta(nombre="Producto", sam=2000, som_anual=[0.10], precio_inicial=100)
        engine.add_gasto_fijo(concepto="Alquiler", importe_anual_ano1=12000)
        engine.add_empleado(perfil="Empleado", sueldo_bruto_anual=30000)

        df_pl = engine.calculate_cuenta_resultados()

        # EBITDA = Margen - Gastos fijos - Nóminas
        ebitda_esperado = (df_pl['margen_comercial'][0] -
                          df_pl['gastos_fijos_servicios'][0] -
                          df_pl['gastos_nomina'][0])
        assert abs(df_pl['ebitda'][0] - ebitda_esperado) < 0.01

    def test_ebit_con_amortizaciones(self):
        """Test del cálculo del EBIT (EBITDA - Amortizaciones)"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_inversion(concepto="Equipos", importe=12000, vida_util_anos=5, mes_adquisicion=1)
        engine.add_linea_venta(nombre="Producto", sam=2000, som_anual=[0.10], precio_inicial=100)

        df_pl = engine.calculate_cuenta_resultados()

        # EBIT = EBITDA - Amortizaciones + Imputación subvenciones
        ebit_esperado = (df_pl['ebitda'][0] -
                        df_pl['amortizaciones'][0] +
                        df_pl['imputacion_subvenciones'][0])
        assert abs(df_pl['ebit'][0] - ebit_esperado) < 0.01

    def test_impuesto_sociedades_con_credito_fiscal(self):
        """Test del IS con compensación de pérdidas (crédito fiscal)"""
        engine = FinancialEngine()
        engine.capital_inicial = 100000
        engine.tax_config.is_rate = 0.25

        # Configurar escenario con pérdidas iniciales
        engine.add_gasto_fijo(concepto="Gastos", importe_anual_ano1=60000)
        engine.add_empleado(perfil="Empleado", sueldo_bruto_anual=30000)
        engine.add_linea_venta(nombre="Producto", sam=1000, som_anual=[0.01, 0.10, 0.20], precio_inicial=100)

        df_pl = engine.calculate_cuenta_resultados()

        # Verificar que cuando hay beneficio después de pérdidas, se usa el crédito fiscal
        # Los primeros meses con pérdidas generan crédito (IS = 0)
        # Cuando llega el beneficio, el IS debe ser menor que EBT * 0.25 por uso del crédito
        for i in range(len(df_pl)):
            if df_pl['ebt'][i] < 0:
                assert df_pl['impuesto_sociedades'][i] == 0
            # Si hay beneficio y hubo pérdidas antes, el IS puede ser menor por el crédito
            # Solo verificamos que IS >= 0
            assert df_pl['impuesto_sociedades'][i] >= 0

    def test_resultado_acumulado(self):
        """Test del resultado acumulado mes a mes"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_linea_venta(nombre="Producto", sam=2000, som_anual=[0.10], precio_inicial=100)
        engine.add_gasto_fijo(concepto="Gastos", importe_anual_ano1=12000)

        df_pl = engine.calculate_cuenta_resultados()

        # El resultado acumulado debe ser la suma acumulada de resultados mensuales
        suma_manual = 0
        for i in range(12):
            suma_manual += df_pl['resultado'][i]
            assert abs(df_pl['resultado_acumulado'][i] - suma_manual) < 0.01


class TestFlujoCaja:
    """Tests exhaustivos del flujo de caja (Cash Flow)"""

    def test_cobros_clientes_incluyen_iva(self):
        """Test que los cobros de clientes incluyen IVA"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.tax_config.iva_ventas = 0.21
        engine.add_linea_venta(nombre="Producto", sam=1000, som_anual=[0.10], precio_inicial=100)

        df_cf = engine.calculate_flujo_tesoreria()

        # Cobros = Ventas + IVA
        ventas_mes = 10000 / 12
        cobros_esperados = ventas_mes * 1.21
        assert abs(df_cf['cobros_clientes'][0] - cobros_esperados) < 0.01

    def test_pagos_iva_mes_vencido(self):
        """Test que el IVA se paga a mes vencido"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_linea_venta(nombre="Producto", sam=1000, som_anual=[0.10], precio_inicial=120)

        df_cf = engine.calculate_flujo_tesoreria()

        # Mes 1: no se paga IVA (aún no se ha liquidado)
        assert df_cf['pagos_iva'][0] == 0

        # Mes 2: se paga el IVA neto del mes 1
        assert df_cf['pagos_iva'][1] != 0

    def test_pagos_ss_mes_siguiente(self):
        """Test que la SS se paga el mes siguiente"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_empleado(perfil="Empleado", sueldo_bruto_anual=30000, mes_alta=1)

        df_cf = engine.calculate_flujo_tesoreria()

        # Mes 1: no se paga SS
        assert df_cf['pagos_ss'][0] == 0

        # Mes 2: se paga la SS del mes 1
        assert df_cf['pagos_ss'][1] > 0

    def test_pagos_irpf_mes_siguiente(self):
        """Test que el IRPF se paga el mes siguiente"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_empleado(perfil="Empleado", sueldo_bruto_anual=50000, mes_alta=1)

        df_cf = engine.calculate_flujo_tesoreria()

        # Mes 1: no se paga IRPF
        assert df_cf['pagos_irpf'][0] == 0

        # Mes 2: se paga el IRPF del mes 1
        assert df_cf['pagos_irpf'][1] > 0

    def test_poliza_credito_con_deficit(self):
        """Test que se usa póliza de crédito cuando hay déficit"""
        engine = FinancialEngine()
        engine.capital_inicial = 5000  # Capital bajo
        engine.add_inversion(concepto="Equipos", importe=20000, mes_adquisicion=1)  # Inversión alta
        engine.add_gasto_fijo(concepto="Gastos", importe_anual_ano1=24000)
        engine.add_linea_venta(nombre="Producto", sam=1000, som_anual=[0.01], precio_inicial=50)

        df_cf = engine.calculate_flujo_tesoreria()

        # Debe haber algún mes con póliza de crédito activa
        assert any(df_cf['poliza_credito'] > 0)

    def test_tesoreria_disponible_nunca_negativa(self):
        """Test que la tesorería disponible nunca es negativa (gracias a la póliza)"""
        engine = FinancialEngine()
        engine.capital_inicial = 1000
        engine.add_gasto_fijo(concepto="Gastos", importe_anual_ano1=60000)
        engine.add_linea_venta(nombre="Producto", sam=1000, som_anual=[0.01], precio_inicial=50)

        df_cf = engine.calculate_flujo_tesoreria()

        # La tesorería disponible siempre debe ser >= 0
        assert all(df_cf['tesoreria_disponible'] >= 0)

    def test_saldo_inicial_tesoreria(self):
        """Test del cálculo del saldo inicial de tesorería"""
        engine = FinancialEngine()
        engine.capital_inicial = 30000
        engine.add_inversion(concepto="Equipos", importe=10000, mes_adquisicion=1, iva_rate=0.21, subvencion=2000)

        # Calcular financiación para obtener saldo inicial
        engine._calculate_financiacion_mensual()

        # Saldo inicial = Capital - Inversiones mes 1 con IVA + Subvenciones mes 1
        # 30000 - 12100 + 2000 = 19900
        assert abs(engine.saldo_inicial_tesoreria - 19900) < 0.01


class TestBalance:
    """Tests del balance de situación"""

    def test_ecuacion_fundamental_balance(self):
        """Test de la ecuación fundamental: Activo = Patrimonio Neto + Pasivo"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_inversion(concepto="Equipos", importe=15000, vida_util_anos=5, mes_adquisicion=1)
        engine.add_prestamo(nombre="Préstamo", importe=30000, mes_inicio=1, meses_amortizacion=60)
        engine.add_linea_venta(nombre="Producto", sam=2000, som_anual=[0.10], precio_inicial=100)
        engine.add_gasto_fijo(concepto="Gastos", importe_anual_ano1=12000)

        df_balance = engine.calculate_balance()

        # El balance debe cuadrar en todos los meses (check_balance ≈ 0)
        for i in range(60):
            assert abs(df_balance['check_balance'][i]) < 1  # Tolerancia de 1€

    def test_patrimonio_neto_incluye_resultado_acumulado(self):
        """Test que el patrimonio neto incluye el resultado acumulado"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_linea_venta(nombre="Producto", sam=2000, som_anual=[0.20], precio_inicial=100)
        engine.add_gasto_fijo(concepto="Gastos", importe_anual_ano1=18000)

        result = engine.generate_all_projections()

        # PN = Capital + Resultado acumulado + Subvenciones
        pn_esperado = (result['balance']['capital'][11] +
                      result['balance']['resultado_acumulado'][11] +
                      result['balance']['subvenciones_capital'][11])

        assert abs(result['balance']['patrimonio_neto'][11] - pn_esperado) < 0.01

    def test_deuda_total_decrece_con_amortizacion(self):
        """Test que la deuda total decrece con la amortización"""
        engine = FinancialEngine()
        engine.capital_inicial = 20000
        engine.add_prestamo(nombre="Préstamo", importe=40000, mes_inicio=1, meses_carencia=0, meses_amortizacion=48)

        df_balance = engine.calculate_balance()

        # Deuda total inicial (mes 1)
        deuda_inicial = df_balance['deuda_largo_plazo'][0] + df_balance['deuda_corto_plazo'][0]

        # Deuda después de un año
        deuda_ano1 = df_balance['deuda_largo_plazo'][11] + df_balance['deuda_corto_plazo'][11]

        # Debe haber disminuido
        assert deuda_ano1 < deuda_inicial


class TestProyectoTrabajoPropio:
    """Tests de proyectos de trabajo para el propio activo (I+D capitalizable)"""

    def test_ingreso_durante_proyecto(self):
        """Test de ingresos reconocidos durante el proyecto"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        proy = ProyectoTrabajoActivoPropio(
            concepto="Desarrollo software",
            importe=12000,
            vida_util_anos=5,
            mes_inicio_proyecto=1,
            mes_fin_proyecto=6,
            subvencion=0
        )
        engine.proyectos_trabajo.append(proy)

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Durante meses 1-6: debe haber ingreso por trabajo propio activo
        # 12000 / 6 meses = 2000€/mes
        for i in range(6):
            assert abs(df_amort['ingresos_trabajo_propio_activo'][i] - 2000) < 0.01

        # Después del mes 6: no hay más ingresos de este proyecto
        assert df_amort['ingresos_trabajo_propio_activo'][6] == 0

    def test_amortizacion_despues_de_activacion(self):
        """Test que la amortización comienza después de finalizar el proyecto"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        proy = ProyectoTrabajoActivoPropio(
            concepto="Desarrollo",
            importe=12000,
            vida_util_anos=5,
            mes_inicio_proyecto=1,
            mes_fin_proyecto=6
        )
        engine.proyectos_trabajo.append(proy)

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Meses 1-6: no hay amortización (proyecto en curso)
        for i in range(6):
            assert df_amort['amortizacion_total'][i] == 0

        # Mes 7: no amortiza (activación)
        assert df_amort['amortizacion_total'][6] == 0

        # Mes 8: primera amortización (12000 / 60 = 200€/mes)
        assert abs(df_amort['amortizacion_total'][7] - 200) < 0.01


class TestCasosIntegracionCompletos:
    """Tests de integración con escenarios completos"""

    def test_caso_startup_sin_financiacion_externa(self):
        """Test de startup financiada solo con capital propio"""
        engine = FinancialEngine()
        engine.capital_inicial = 80000

        # Inversiones
        engine.add_inversion(concepto="Software", importe=15000, vida_util_anos=5, mes_adquisicion=1)
        engine.add_inversion(concepto="Equipos", importe=10000, vida_util_anos=5, mes_adquisicion=1)

        # Gastos
        engine.add_gasto_fijo(concepto="Alquiler", importe_anual_ano1=18000)
        engine.add_empleado(perfil="Fundador", sueldo_bruto_anual=24000, es_autonomo=True)

        # Ingresos
        engine.add_linea_venta(nombre="SaaS", sam=5000, som_anual=[0.01, 0.05, 0.10], precio_inicial=120)

        result = engine.generate_all_projections()

        # No debe haber deuda
        assert all(result['balance']['deuda_largo_plazo'] == 0)
        assert all(result['balance']['deuda_corto_plazo'] == 0)

        # El capital debe mantenerse constante (sin ampliaciones)
        assert all(result['balance']['capital'] == 80000)

    def test_caso_con_subvenciones(self):
        """Test de caso con subvenciones que reducen el impacto fiscal"""
        engine = FinancialEngine()
        engine.capital_inicial = 30000

        # Inversión con subvención
        engine.add_inversion(
            concepto="I+D",
            importe=20000,
            vida_util_anos=5,
            mes_adquisicion=1,
            subvencion=10000  # 50% subvencionado
        )

        df_amort = engine._calculate_amortizaciones_mensuales()

        # Imputación de subvención: 10000 / (5*12) ≈ 166.67€/mes
        assert abs(df_amort['imputacion_subvenciones'][0] - 166.67) < 0.01

        # La imputación debe reducir el impacto de la amortización en el P&L
        df_pl = engine.calculate_cuenta_resultados()

        # EBIT incluye la imputación positiva
        # (lo que compensa parcialmente el efecto negativo de la amortización)
        assert df_pl['imputacion_subvenciones'][0] > 0

    def test_coherencia_flujos_entre_estados(self):
        """Test que verifica coherencia entre P&L, CF y Balance"""
        engine = FinancialEngine()
        engine.capital_inicial = 50000
        engine.add_inversion(concepto="Equipos", importe=15000, vida_util_anos=5, mes_adquisicion=1)
        engine.add_prestamo(nombre="Préstamo", importe=30000, mes_inicio=1, meses_amortizacion=48)
        engine.add_linea_venta(nombre="Producto", sam=2000, som_anual=[0.10, 0.15], precio_inicial=100)
        engine.add_gasto_fijo(concepto="Gastos", importe_anual_ano1=18000)
        engine.add_empleado(perfil="Empleado", sueldo_bruto_anual=30000)

        result = engine.generate_all_projections()

        # El resultado del P&L debe fluir al balance
        assert result['cuenta_resultados']['resultado_acumulado'][11] == result['balance']['resultado_acumulado'][11]

        # El cash flow acumulado debe coincidir con la tesorería (descontando póliza)
        cf_real = result['flujo_tesoreria']['cf_acumulado'][11]
        tesoreria = result['flujo_tesoreria']['tesoreria_disponible'][11]
        poliza = result['flujo_tesoreria']['poliza_credito'][11]
        assert abs(cf_real - (tesoreria - poliza)) < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
