"""
Motor de cálculo financiero - PEF ToolBoard v2.0
Implementa los algoritmos de cálculo de la metodología PEF ToolBoard
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
try:
    from ..config import Config
except ImportError:
    from config import Config


@dataclass
class Inversion:
    """Representa una inversión (CAPEX)"""
    concepto: str
    importe: float
    iva_rate: float = 0.21
    vida_util_anos: int = 5
    mes_adquisicion: int = 1
    subvencion: float = 0.0

    @property
    def iva(self) -> float:
        return self.importe * self.iva_rate

    @property
    def total_con_iva(self) -> float:
        return self.importe + self.iva

    @property
    def amortizacion_mensual(self) -> float:
        if self.vida_util_anos <= 0:
            return 0
        return self.importe / (self.vida_util_anos * 12)

    @property
    def mes_fin_amortizacion(self) -> int:
        return self.vida_util_anos * 12 + self.mes_adquisicion


@dataclass
class ProyectoTrabajoActivoPropio:
    """Representa un proyecto de trabajo para el propio activo (I+D interno capitalizable)"""
    concepto: str
    importe: float
    vida_util_anos: int = 5
    mes_inicio_proyecto: int = 1
    mes_fin_proyecto: int = 12
    subvencion: float = 0.0

    @property
    def duracion_meses(self) -> int:
        return self.mes_fin_proyecto - self.mes_inicio_proyecto + 1

    @property
    def importe_medio_mensual(self) -> float:
        if self.duracion_meses <= 0:
            return 0
        return self.importe / self.duracion_meses

    @property
    def mes_inicio_amortizacion(self) -> int:
        return self.mes_fin_proyecto + 1

    @property
    def mes_fin_amortizacion(self) -> int:
        return self.mes_inicio_amortizacion + self.vida_util_anos * 12

    @property
    def amortizacion_mensual(self) -> float:
        if self.vida_util_anos <= 0:
            return 0
        return self.importe / (self.vida_util_anos * 12)

    @property
    def subvencion_amortizacion_mensual(self) -> float:
        if self.vida_util_anos <= 0:
            return 0
        return self.subvencion / (self.vida_util_anos * 12)


@dataclass
class Prestamo:
    """Representa un préstamo"""
    nombre: str
    importe: float
    mes_inicio: int = 1
    meses_carencia: int = 0
    meses_amortizacion: int = 60
    interes_anual: float = 0.05

    @property
    def mes_final(self) -> int:
        return self.mes_inicio + self.meses_carencia + self.meses_amortizacion

    @property
    def interes_mensual(self) -> float:
        return self.interes_anual / 12

    def get_cuota_mensual(self, mes: int) -> Dict[str, float]:
        """Calcula la cuota de un mes específico (capital + intereses)"""
        # El primer pago es un mes después del inicio (como en el Excel)
        # Antes del mes de inicio + 1 no hay cuota
        if mes <= self.mes_inicio:
            return {'capital': 0, 'intereses': 0, 'cuota': 0}

        # Calcular mes relativo (empieza en 1 desde el primer pago)
        mes_relativo = mes - self.mes_inicio

        # Durante carencia: solo intereses
        if mes_relativo <= self.meses_carencia:
            intereses = self.importe * self.interes_mensual
            return {'capital': 0, 'intereses': intereses, 'cuota': intereses}

        # Después de carencia: cuota francesa
        if mes_relativo > self.meses_carencia + self.meses_amortizacion:
            return {'capital': 0, 'intereses': 0, 'cuota': 0}

        # Calcular cuota con sistema francés
        if self.interes_mensual > 0:
            cuota = self.importe * (self.interes_mensual * (1 + self.interes_mensual)**self.meses_amortizacion) / \
                    ((1 + self.interes_mensual)**self.meses_amortizacion - 1)
        else:
            cuota = self.importe / self.meses_amortizacion

        # Calcular capital pendiente al inicio de este período
        meses_pagados = mes_relativo - self.meses_carencia - 1
        if self.interes_mensual > 0:
            capital_pendiente = self.importe * ((1 + self.interes_mensual)**self.meses_amortizacion -
                                                 (1 + self.interes_mensual)**meses_pagados) / \
                                ((1 + self.interes_mensual)**self.meses_amortizacion - 1)
        else:
            capital_pendiente = self.importe - (meses_pagados * cuota)

        intereses = capital_pendiente * self.interes_mensual
        capital = cuota - intereses

        return {'capital': capital, 'intereses': intereses, 'cuota': cuota}


@dataclass
class Empleado:
    """Representa un empleado o perfil de nómina"""
    perfil: str
    num_trabajadores: int = 1
    mes_alta: int = 1
    mes_baja: int = 60
    sueldo_bruto_anual: float = 0
    es_autonomo: bool = False
    etapa: int = 1  # Etapa de contratación (1, 2 o 3)

    def calcular_costes(self, config: 'TaxConfig', sueldo_override: float = None) -> Dict[str, float]:
        """Calcula los costes asociados al empleado"""
        sueldo = sueldo_override if sueldo_override is not None else self.sueldo_bruto_anual

        if self.es_autonomo:
            # Régimen especial autónomos
            base_cotizacion = min(sueldo, config.ss_tope_autonomos)
            ss_empresa = base_cotizacion * config.ss_autonomos_rate
            ss_trabajador = 0
        else:
            # Régimen general
            base_cotizacion = min(sueldo, config.ss_tope_general)
            ss_empresa = base_cotizacion * config.ss_empresa_rate
            ss_trabajador = base_cotizacion * config.ss_trabajador_rate

        # IRPF por tramos
        if sueldo < 15000:
            irpf = sueldo * config.irpf_bajo
        elif sueldo < 90000:
            irpf = sueldo * config.irpf_medio
        else:
            irpf = sueldo * config.irpf_alto

        return {
            'sueldo_bruto': sueldo,
            'ss_empresa': ss_empresa,
            'ss_trabajador': ss_trabajador,
            'ss_total': ss_empresa + ss_trabajador,
            'irpf': irpf,
            'coste_empresa': sueldo + ss_empresa,
            'neto_trabajador': sueldo - ss_trabajador - irpf
        }

    def get_sueldo_ano(self, ano: int, incrementos: Dict[int, float]) -> float:
        """Calcula el sueldo para un año específico aplicando incrementos"""
        sueldo = self.sueldo_bruto_anual
        # Incrementos según etapa:
        # Etapa 1 -> incremento aplicado en año 2
        # Etapa 2 -> incremento aplicado en año 3
        # Etapa 3 -> incremento aplicado en año 4 y siguientes
        if ano >= 2 and 1 in incrementos:
            sueldo *= (1 + incrementos[1])
        if ano >= 3 and 2 in incrementos:
            sueldo *= (1 + incrementos[2])
        if ano >= 4 and 3 in incrementos:
            # Año 4 y siguientes usan incremento de etapa 3
            for _ in range(ano - 3):
                sueldo *= (1 + incrementos[3])
        return sueldo


@dataclass
class LineaVenta:
    """Representa una línea de producto/servicio"""
    nombre: str
    sam: int  # Serviceable Addressable Market
    som_anual: List[float] = field(default_factory=lambda: [0.01, 0.05, 0.10, 0.15, 0.20])
    precio_inicial: float = 100
    incremento_precio_anual: List[float] = field(default_factory=lambda: [0, 0.04, 0.02, 0.03, 0.03])
    cv_produccion: float = 0.0  # % coste variable producción
    cv_adquisicion: float = 0.0  # % coste variable adquisición
    comisiones: float = 0.0  # % comisiones

    @property
    def coste_variable_total(self) -> float:
        """Porcentaje total de costes variables sobre ventas"""
        return self.cv_produccion + self.cv_adquisicion + self.comisiones

    def get_unidades_ano(self, ano: int) -> int:
        """Calcula unidades vendidas en un año (1-5)"""
        if ano < 1 or ano > 5:
            return 0
        som = self.som_anual[ano - 1] if ano <= len(self.som_anual) else self.som_anual[-1]
        return int(self.sam * som)

    def get_precio_ano(self, ano: int) -> float:
        """Calcula el precio en un año específico"""
        precio = self.precio_inicial
        for i in range(1, min(ano, len(self.incremento_precio_anual))):
            precio *= (1 + self.incremento_precio_anual[i])
        return precio

    def get_ventas_ano(self, ano: int) -> float:
        """Calcula las ventas totales de un año"""
        return self.get_unidades_ano(ano) * self.get_precio_ano(ano)


@dataclass
class GastoFijo:
    """Representa un gasto fijo (OPEX)"""
    concepto: str
    importe_anual_ano1: float = 0.0
    iva_rate: float = 0.21
    incremento_anual: float = 0.0  # Incremento porcentual anual (decimal, ej: 0.03 = 3%)
    importes_anuales: List[float] = field(default_factory=list)  # Importes explícitos por año [año1..año5]

    def get_importe_ano(self, ano: int) -> float:
        """Calcula el importe para un año específico"""
        # Si hay importes explícitos por año, usar esos
        if self.importes_anuales and 1 <= ano <= len(self.importes_anuales):
            return self.importes_anuales[ano - 1]
        # Fallback: calcular con incremento compuesto
        if ano == 1:
            return self.importe_anual_ano1
        return self.importe_anual_ano1 * ((1 + self.incremento_anual) ** (ano - 1))

    def get_iva_ano(self, ano: int) -> float:
        return self.get_importe_ano(ano) * self.iva_rate


@dataclass
class TaxConfig:
    """Configuración fiscal"""
    is_rate: float = 0.25  # Impuesto de Sociedades
    iva_compras: float = 0.21
    iva_ventas: float = 0.21
    iva_inversiones: float = 0.21
    ss_autonomos_rate: float = 0.15
    ss_empresa_rate: float = 0.33
    ss_trabajador_rate: float = 0.0647
    ss_tope_autonomos: float = 56640
    ss_tope_general: float = 56640
    irpf_bajo: float = 0.0
    irpf_medio: float = 0.20
    irpf_alto: float = 0.40


class FinancialEngine:
    """
    Motor de cálculo para el Plan Económico-Financiero
    Basado en la metodología PEF ToolBoard v2.0
    """

    def __init__(self):
        """Inicializa el motor de cálculo"""
        self.months = Config.PROJECTION_MONTHS
        self.years = Config.PROJECTION_YEARS
        self.tax_config = TaxConfig()

        # Datos de entrada
        self.inversiones: List[Inversion] = []
        self.proyectos_trabajo: List[ProyectoTrabajoActivoPropio] = []
        self.prestamos: List[Prestamo] = []
        self.capital_inicial: float = 0
        self.ampliaciones: List[Dict] = []
        self.poliza_credito_interes: float = 0.03
        self.gastos_fijos: List[GastoFijo] = []
        self.empleados: List[Empleado] = []
        self.incrementos_salariales: Dict[int, float] = {}  # {etapa: incremento decimal}
        self.lineas_venta: List[LineaVenta] = []

        # Estados financieros resultantes (DataFrames mensuales)
        self.df_ventas: Optional[pd.DataFrame] = None
        self.df_gastos: Optional[pd.DataFrame] = None
        self.df_amortizaciones: Optional[pd.DataFrame] = None
        self.df_nominas: Optional[pd.DataFrame] = None
        self.df_financiacion: Optional[pd.DataFrame] = None
        self.cuenta_resultados: Optional[pd.DataFrame] = None
        self.flujo_tesoreria: Optional[pd.DataFrame] = None
        self.balance: Optional[pd.DataFrame] = None
        self.ratios: Optional[Dict[str, Any]] = None

    def set_tax_config(self, **kwargs):
        """Actualiza la configuración fiscal"""
        for key, value in kwargs.items():
            if hasattr(self.tax_config, key):
                setattr(self.tax_config, key, value)

    def add_inversion(self, **kwargs):
        """Añade una inversión"""
        self.inversiones.append(Inversion(**kwargs))

    def add_prestamo(self, **kwargs):
        """Añade un préstamo"""
        self.prestamos.append(Prestamo(**kwargs))

    def add_gasto_fijo(self, **kwargs):
        """Añade un gasto fijo"""
        self.gastos_fijos.append(GastoFijo(**kwargs))

    def add_empleado(self, **kwargs):
        """Añade un empleado"""
        self.empleados.append(Empleado(**kwargs))

    def add_linea_venta(self, **kwargs):
        """Añade una línea de venta"""
        self.lineas_venta.append(LineaVenta(**kwargs))

    def set_inversiones(self, inversiones: List[Dict[str, Any]]):
        """Establece las inversiones del proyecto desde lista de dicts"""
        self.inversiones = []
        for inv in inversiones:
            self.add_inversion(**inv)

    def set_proyectos_trabajo(self, proyectos: List[Dict[str, Any]]):
        """Establece los proyectos de trabajo para el propio activo desde lista de dicts"""
        self.proyectos_trabajo = []
        for p in proyectos:
            self.proyectos_trabajo.append(ProyectoTrabajoActivoPropio(**p))

    def set_financiacion(self, financiacion: Dict[str, Any]):
        """Establece las fuentes de financiación"""
        self.capital_inicial = financiacion.get('capital_inicial', 0)
        self.ampliaciones = financiacion.get('ampliaciones', [])  # [{mes, importe}]
        self.poliza_credito_interes = financiacion.get('poliza_interes', 0.03)

        self.prestamos = []
        for prestamo in financiacion.get('prestamos', []):
            self.add_prestamo(**prestamo)

    def set_gastos_operativos(self, gastos_fijos: List[Dict],
                              empleados: List[Dict]):
        """Establece los gastos operativos (OPEX)"""
        self.gastos_fijos = []
        for gasto in gastos_fijos:
            self.add_gasto_fijo(**gasto)

        self.empleados = []
        for emp in empleados:
            self.add_empleado(**emp)

    def set_ingresos(self, lineas: List[Dict[str, Any]]):
        """Establece las proyecciones de ingresos"""
        self.lineas_venta = []
        for linea in lineas:
            self.add_linea_venta(**linea)

    def _mes_a_ano(self, mes: int) -> int:
        """Convierte un mes (1-60) a año (1-5)"""
        return ((mes - 1) // 12) + 1

    def _calculate_ventas_mensuales(self) -> pd.DataFrame:
        """Calcula las ventas mensuales por línea de producto"""
        data = {
            'mes': list(range(1, self.months + 1)),
            'ventas_totales': [0.0] * self.months,
            'costes_variables': [0.0] * self.months,
            'iva_repercutido': [0.0] * self.months,
        }

        for linea in self.lineas_venta:
            linea_ventas = []
            linea_cv = []
            for mes in range(1, self.months + 1):
                ano = self._mes_a_ano(mes)
                ventas_ano = linea.get_ventas_ano(ano)
                ventas_mes = ventas_ano / 12
                cv_mes = ventas_mes * linea.coste_variable_total
                linea_ventas.append(ventas_mes)
                linea_cv.append(cv_mes)

            data[f'ventas_{linea.nombre}'] = linea_ventas
            data[f'cv_{linea.nombre}'] = linea_cv

            for i in range(self.months):
                data['ventas_totales'][i] += linea_ventas[i]
                data['costes_variables'][i] += linea_cv[i]

        # Calcular IVA repercutido
        for i in range(self.months):
            data['iva_repercutido'][i] = data['ventas_totales'][i] * self.tax_config.iva_ventas

        return pd.DataFrame(data)

    def _calculate_gastos_fijos_mensuales(self) -> pd.DataFrame:
        """Calcula los gastos fijos mensuales"""
        data = {
            'mes': list(range(1, self.months + 1)),
            'gastos_fijos_totales': [0.0] * self.months,
            'iva_soportado_gastos': [0.0] * self.months,
        }

        for gasto in self.gastos_fijos:
            gasto_mensual = []
            iva_mensual = []
            for mes in range(1, self.months + 1):
                ano = self._mes_a_ano(mes)
                importe_ano = gasto.get_importe_ano(ano)
                importe_mes = importe_ano / 12
                iva_mes = gasto.get_iva_ano(ano) / 12
                gasto_mensual.append(importe_mes)
                iva_mensual.append(iva_mes)

            data[f'gasto_{gasto.concepto}'] = gasto_mensual

            for i in range(self.months):
                data['gastos_fijos_totales'][i] += gasto_mensual[i]
                data['iva_soportado_gastos'][i] += iva_mensual[i]

        return pd.DataFrame(data)

    def _calculate_nominas_mensuales(self) -> pd.DataFrame:
        """Calcula las nóminas mensuales"""
        data = {
            'mes': list(range(1, self.months + 1)),
            'sueldos_brutos': [0.0] * self.months,
            'ss_empresa': [0.0] * self.months,
            'ss_trabajador': [0.0] * self.months,
            'irpf': [0.0] * self.months,
            'coste_empresa_total': [0.0] * self.months,
        }

        for emp in self.empleados:
            for mes in range(1, self.months + 1):
                # Solo si el empleado está activo en ese mes
                if emp.mes_alta <= mes <= emp.mes_baja:
                    # Calcular el año correspondiente al mes (1-5)
                    ano = self._mes_a_ano(mes)
                    
                    # Obtener sueldo para ese año, aplicando incrementos
                    sueldo_bruto_ano = emp.get_sueldo_ano(ano, self.incrementos_salariales)
                    
                    # Actualizar sueldo base del empleado temporalmente para este cálculo
                    sueldo_original = emp.sueldo_bruto_anual
                    emp.sueldo_bruto_anual = sueldo_bruto_ano
                    
                    # Calcular costes con el sueldo ajustado por año
                    costes = emp.calcular_costes(self.tax_config)
                    
                    # Restaurar sueldo original
                    emp.sueldo_bruto_anual = sueldo_original
                    
                    # Valores mensuales
                    sueldo_mensual = costes['sueldo_bruto'] / 12
                    ss_empresa_mensual = costes['ss_empresa'] / 12
                    ss_trabajador_mensual = costes['ss_trabajador'] / 12
                    irpf_mensual = costes['irpf'] / 12
                    coste_empresa_mensual = costes['coste_empresa'] / 12

                    idx = mes - 1
                    num = emp.num_trabajadores
                    data['sueldos_brutos'][idx] += sueldo_mensual * num
                    data['ss_empresa'][idx] += ss_empresa_mensual * num
                    data['ss_trabajador'][idx] += ss_trabajador_mensual * num
                    data['irpf'][idx] += irpf_mensual * num
                    data['coste_empresa_total'][idx] += coste_empresa_mensual * num

        return pd.DataFrame(data)

    def _calculate_amortizaciones_mensuales(self) -> pd.DataFrame:
        """Calcula las amortizaciones mensuales"""
        data = {
            'mes': list(range(1, self.months + 1)),
            'amortizacion_total': [0.0] * self.months,
            'inmovilizado_neto': [0.0] * self.months,
            'iva_soportado_inversiones': [0.0] * self.months,
            'ingresos_trabajo_propio_activo': [0.0] * self.months,
            'imputacion_subvenciones': [0.0] * self.months,
        }

        # Calcular amortización acumulada e inmovilizado
        amortizacion_acumulada = 0.0

        for mes in range(1, self.months + 1):
            idx = mes - 1
            amort_mes = 0.0
            iva_mes = 0.0
            imputacion_sub_mes = 0.0

            # Inversiones normales (amortización empieza el mismo mes de adquisición)
            for inv in self.inversiones:
                if inv.mes_adquisicion <= mes <= inv.mes_fin_amortizacion:
                    amort_mes += inv.amortizacion_mensual
                    # Imputación de subvención de esta inversión
                    if inv.subvencion > 0 and inv.vida_util_anos > 0:
                        imputacion_sub_mes += inv.subvencion / (inv.vida_util_anos * 12)

                if inv.mes_adquisicion == mes:
                    iva_mes += inv.iva

            # Proyectos de trabajo para el propio activo
            for proy in self.proyectos_trabajo:
                # Amortización: el activo se activa en mes_fin+1, primera cuota en mes_fin+2
                if proy.mes_inicio_amortizacion < mes <= proy.mes_fin_amortizacion:
                    amort_mes += proy.amortizacion_mensual
                    imputacion_sub_mes += proy.subvencion_amortizacion_mensual

                # Ingreso por trabajo propio activo durante el periodo de trabajo
                if proy.mes_inicio_proyecto <= mes <= proy.mes_fin_proyecto:
                    data['ingresos_trabajo_propio_activo'][idx] += proy.importe_medio_mensual

            amortizacion_acumulada += amort_mes
            data['amortizacion_total'][idx] = amort_mes
            data['imputacion_subvenciones'][idx] = imputacion_sub_mes

            # Inmovilizado neto dinámico: inversiones activas + proyectos trabajo
            total_activos_mes = 0.0
            for inv in self.inversiones:
                if inv.mes_adquisicion <= mes:
                    total_activos_mes += inv.importe
            for proy in self.proyectos_trabajo:
                if proy.mes_inicio_proyecto <= mes:
                    if mes <= proy.mes_fin_proyecto:
                        # En curso: importe proporcional acumulado
                        meses_transcurridos = mes - proy.mes_inicio_proyecto + 1
                        total_activos_mes += proy.importe_medio_mensual * meses_transcurridos
                    else:
                        # Activado: importe total
                        total_activos_mes += proy.importe

            data['inmovilizado_neto'][idx] = total_activos_mes - amortizacion_acumulada
            data['iva_soportado_inversiones'][idx] = iva_mes

        return pd.DataFrame(data)

    def _calculate_financiacion_mensual(self) -> pd.DataFrame:
        """Calcula los flujos de financiación mensuales"""
        data = {
            'mes': list(range(1, self.months + 1)),
            'entrada_capital': [0.0] * self.months,
            'entrada_prestamos': [0.0] * self.months,
            'pago_capital_prestamos': [0.0] * self.months,
            'pago_intereses': [0.0] * self.months,
            'deuda_largo_plazo': [0.0] * self.months,
            'deuda_corto_plazo': [0.0] * self.months,
        }

        # Saldo inicial (mes 0): capital inicial - inversiones del mes 1 con IVA
        # Las inversiones del mes 1 se pagan en el mes 0 (como en el Excel)
        # Las subvenciones se cobran en cobros_subvenciones en su mes de recepción
        # Los préstamos entran en su mes de inicio
        self.saldo_inicial_tesoreria = self.capital_inicial
        for inv in self.inversiones:
            if inv.mes_adquisicion == 1:
                self.saldo_inicial_tesoreria -= inv.total_con_iva

        # Ampliaciones de capital - entran como flujo en su mes
        for amp in self.ampliaciones:
            mes = amp.get('mes', 13)
            importe = amp.get('importe', 0)
            if importe > 0 and 1 <= mes <= self.months:
                data['entrada_capital'][mes - 1] += importe

        # Préstamos - entran como flujo en su mes de inicio
        for prestamo in self.prestamos:
            if prestamo.mes_inicio <= self.months:
                data['entrada_prestamos'][prestamo.mes_inicio - 1] += prestamo.importe

            # Cuotas mensuales
            capital_pendiente = prestamo.importe
            for mes in range(1, self.months + 1):
                cuota = prestamo.get_cuota_mensual(mes)
                idx = mes - 1
                data['pago_capital_prestamos'][idx] += cuota['capital']
                data['pago_intereses'][idx] += cuota['intereses']
                capital_pendiente -= cuota['capital']

                # Clasificar deuda LP/CP:
                # CP = próximos 12 meses de amortización de principal
                # LP = resto del saldo pendiente
                proximos_12 = sum(
                    prestamo.get_cuota_mensual(m)['capital']
                    for m in range(mes + 1, min(mes + 13, self.months + 1))
                )
                saldo = max(0, capital_pendiente)
                cp = min(proximos_12, saldo)
                lp = saldo - cp
                data['deuda_largo_plazo'][idx] += lp
                data['deuda_corto_plazo'][idx] += cp

        return pd.DataFrame(data)

    def calculate_cuenta_resultados(self) -> pd.DataFrame:
        """
        Calcula la cuenta de resultados (P&L)
        Incluye intereses de póliza de crédito cuando hay déficit de tesorería
        """
        # Calcular componentes
        self.df_ventas = self._calculate_ventas_mensuales()
        self.df_gastos = self._calculate_gastos_fijos_mensuales()
        self.df_nominas = self._calculate_nominas_mensuales()
        self.df_amortizaciones = self._calculate_amortizaciones_mensuales()

        # Calcular financiación para gastos financieros de préstamos
        self.df_financiacion = self._calculate_financiacion_mensual()

        # Calcular flujo de tesorería preliminar para determinar uso de póliza
        # y sus intereses asociados (guardar como atributo para usar en flujo_tesoreria)
        self.intereses_poliza = self._calculate_intereses_poliza()

        data = {
            'mes': list(range(1, self.months + 1)),
            'ingresos': self.df_ventas['ventas_totales'].values.copy(),
            'ingresos_trabajo_propio_activo': self.df_amortizaciones['ingresos_trabajo_propio_activo'].values.copy(),
            'costes_variables': self.df_ventas['costes_variables'].values.copy(),
            'margen_comercial': [0.0] * self.months,
            'gastos_fijos_servicios': self.df_gastos['gastos_fijos_totales'].values.copy(),
            'gastos_nomina': self.df_nominas['coste_empresa_total'].values.copy(),
            'ebitda': [0.0] * self.months,
            'amortizaciones': self.df_amortizaciones['amortizacion_total'].values.copy(),
            'imputacion_subvenciones': self.df_amortizaciones['imputacion_subvenciones'].values.copy(),
            'ebit': [0.0] * self.months,
            'gastos_financieros': [0.0] * self.months,
            'ebt': [0.0] * self.months,
            'impuesto_sociedades': [0.0] * self.months,
            'resultado': [0.0] * self.months,
            'resultado_acumulado': [0.0] * self.months,
        }

        # Gastos financieros = intereses préstamos + intereses póliza de crédito
        for i in range(self.months):
            data['gastos_financieros'][i] = (
                self.df_financiacion['pago_intereses'][i] + self.intereses_poliza[i]
            )

        resultado_acum = 0.0
        credito_fiscal_pl = 0.0  # Crédito fiscal acumulado de pérdidas anteriores
        self._credito_fiscal_pl = [0.0] * self.months  # Saldo restante por mes
        for i in range(self.months):
            # Margen comercial = Ingresos + Ingresos trabajo propio activo - Costes variables
            data['margen_comercial'][i] = (data['ingresos'][i] +
                                            data['ingresos_trabajo_propio_activo'][i] -
                                            data['costes_variables'][i])

            # EBITDA = Margen - Gastos fijos - Nóminas
            data['ebitda'][i] = (data['margen_comercial'][i] -
                                 data['gastos_fijos_servicios'][i] -
                                 data['gastos_nomina'][i])

            # EBIT = EBITDA - Amortizaciones + Imputación subvenciones
            data['ebit'][i] = (data['ebitda'][i] - data['amortizaciones'][i] +
                               data['imputacion_subvenciones'][i])

            # EBT = EBIT - Gastos financieros
            data['ebt'][i] = data['ebit'][i] - data['gastos_financieros'][i]

            # Impuesto de Sociedades con crédito fiscal por pérdidas (como en el Excel)
            # Meses con pérdida generan crédito; meses con beneficio usan el crédito primero
            is_bruto = data['ebt'][i] * self.tax_config.is_rate
            if is_bruto <= 0:
                credito_fiscal_pl += (-is_bruto)  # Acumular crédito de la pérdida
                data['impuesto_sociedades'][i] = 0.0
            else:
                credito_usado = min(is_bruto, credito_fiscal_pl)
                credito_fiscal_pl -= credito_usado
                data['impuesto_sociedades'][i] = is_bruto - credito_usado
            self._credito_fiscal_pl[i] = credito_fiscal_pl

            # Resultado = EBT - IS
            data['resultado'][i] = data['ebt'][i] - data['impuesto_sociedades'][i]

            # Resultado acumulado
            resultado_acum += data['resultado'][i]
            data['resultado_acumulado'][i] = resultado_acum

        self.cuenta_resultados = pd.DataFrame(data)
        return self.cuenta_resultados

    def _calculate_intereses_poliza(self) -> List[float]:
        """
        Calcula los intereses de la póliza de crédito basándose en el déficit de tesorería.
        Replica el cálculo completo del cash flow para determinar cuándo se necesita póliza.
        """
        intereses = [0.0] * self.months

        # IVA de inversiones del mes 0 (pagado en saldo inicial, recuperado en mes 1 directamente)
        iva_inv_mes0 = sum(inv.iva for inv in self.inversiones if inv.mes_adquisicion == 1)

        # Pre-calcular IVA neto mensual (IVA repercutido - IVA soportado operativo)
        iva_neto_mensual = [0.0] * self.months
        for i in range(self.months):
            iva_rep = self.df_ventas['iva_repercutido'][i]
            iva_inv = self.df_amortizaciones['iva_soportado_inversiones'][i]
            if i == 0:
                iva_inv -= iva_inv_mes0  # Ya gestionado directamente en mes 1
            iva_sop = (self.df_gastos['iva_soportado_gastos'][i] +
                      iva_inv +
                      self.df_ventas['costes_variables'][i] * self.tax_config.iva_compras)
            iva_neto_mensual[i] = iva_rep - iva_sop

        # Pre-calcular IS preliminar mensual con crédito fiscal (sin intereses póliza)
        # Replica la lógica de calculate_cuenta_resultados para tener IS ajustado por crédito
        is_ebt_bruto = [0.0] * self.months
        for i in range(self.months):
            ingresos_mes = self.df_ventas['ventas_totales'][i]
            tpa_mes = self.df_amortizaciones['ingresos_trabajo_propio_activo'][i]
            cv_mes = self.df_ventas['costes_variables'][i]
            gf_mes = self.df_gastos['gastos_fijos_totales'][i]
            nom_mes = self.df_nominas['coste_empresa_total'][i]
            amort_mes = self.df_amortizaciones['amortizacion_total'][i]
            subv_mes = self.df_amortizaciones['imputacion_subvenciones'][i]
            int_prest_mes = self.df_financiacion['pago_intereses'][i]

            ebitda_mes = ingresos_mes + tpa_mes - cv_mes - gf_mes - nom_mes
            ebit_mes = ebitda_mes - amort_mes + subv_mes
            ebt_mes = ebit_mes - int_prest_mes
            is_ebt_bruto[i] = ebt_mes * self.tax_config.is_rate  # puede ser negativo

        # Aplicar crédito fiscal acumulado (mismo mecanismo que cuenta_resultados)
        is_preliminar = [0.0] * self.months
        cf_credito = 0.0
        for i in range(self.months):
            bruto = is_ebt_bruto[i]
            if bruto <= 0:
                cf_credito += (-bruto)
                is_preliminar[i] = 0.0
            else:
                usado = min(bruto, cf_credito)
                cf_credito -= usado
                is_preliminar[i] = bruto - usado

        # Calcular cash flow preliminar para determinar déficit
        cf_acum = getattr(self, 'saldo_inicial_tesoreria', 0.0)
        saldo_poliza_anterior = 0.0

        for i in range(self.months):
            # Cobros de clientes (ventas + IVA)
            cobros = (self.df_ventas['ventas_totales'][i] +
                     self.df_ventas['iva_repercutido'][i])

            # Pagos proveedores (costes variables + IVA)
            cv = self.df_ventas['costes_variables'][i]
            pagos_prov = cv + (cv * self.tax_config.iva_compras)

            # Pagos gastos fijos (+ IVA)
            pagos_gf = (self.df_gastos['gastos_fijos_totales'][i] +
                       self.df_gastos['iva_soportado_gastos'][i])

            # Pagos nóminas (neto a pagar)
            pagos_nom = (self.df_nominas['sueldos_brutos'][i] -
                        self.df_nominas['ss_trabajador'][i] -
                        self.df_nominas['irpf'][i])

            # Pagos SS (mes siguiente)
            pagos_ss = 0.0
            if i > 0:
                pagos_ss = (self.df_nominas['ss_empresa'][i-1] +
                           self.df_nominas['ss_trabajador'][i-1])

            # Pagos IRPF (mes siguiente)
            pagos_irpf = 0.0
            if i > 0:
                pagos_irpf = self.df_nominas['irpf'][i-1]

            # Pagos IVA: mes 1 recupera el IVA de inversiones del mes 0; resto con 1 mes de retraso
            if i == 0:
                pagos_iva = -iva_inv_mes0
            elif i > 0:
                pagos_iva = iva_neto_mensual[i - 1]
            else:
                pagos_iva = 0.0

            # Pagos inversiones (las del mes 1 ya se pagaron en el mes 0, saldo inicial)
            pagos_inv = 0.0
            for inv in self.inversiones:
                if inv.mes_adquisicion == i + 1 and inv.mes_adquisicion > 1:
                    pagos_inv += inv.total_con_iva

            # Pagos IS: 1 mes de retraso (como en el Excel)
            pagos_is = 0.0
            if i > 0 and is_preliminar[i - 1] > 0:
                pagos_is = is_preliminar[i - 1]

            # Entradas financiación
            entrada_cap = self.df_financiacion['entrada_capital'][i]
            entrada_prest = self.df_financiacion['entrada_prestamos'][i]
            pago_prest = self.df_financiacion['pago_capital_prestamos'][i]
            pago_int = self.df_financiacion['pago_intereses'][i]

            # Cobros subvenciones: todas las inversiones en su mes (incluyendo mes 1)
            cobros_sub = 0.0
            for inv in self.inversiones:
                if inv.subvencion > 0 and inv.mes_adquisicion == i + 1:
                    cobros_sub += inv.subvencion
            for proy in self.proyectos_trabajo:
                if proy.subvencion > 0 and proy.mes_fin_proyecto == i + 1:
                    cobros_sub += proy.subvencion

            # Calcular intereses de la póliza del mes anterior (se pagan este mes)
            interes_poliza_mes = 0.0
            if saldo_poliza_anterior > 0:
                interes_poliza_mes = saldo_poliza_anterior * (self.poliza_credito_interes / 12)
            intereses[i] = interes_poliza_mes

            # CF neto del mes (incluyendo todos los componentes)
            cf_mes = (cobros - pagos_prov - pagos_gf - pagos_nom -
                     pagos_ss - pagos_irpf - pagos_iva - pagos_inv -
                     pagos_is +
                     entrada_cap + entrada_prest + cobros_sub - pago_prest - pago_int -
                     interes_poliza_mes)

            cf_acum += cf_mes

            # Actualizar saldo de póliza para el siguiente mes
            if cf_acum < 0:
                saldo_poliza_anterior = abs(cf_acum)
            else:
                saldo_poliza_anterior = 0.0

        return intereses

    def calculate_flujo_tesoreria(self) -> pd.DataFrame:
        """
        Calcula el flujo de tesorería (Cash Flow)
        Diferencia entre cobros y pagos efectivos
        """
        if self.cuenta_resultados is None:
            self.calculate_cuenta_resultados()

        data = {
            'mes': list(range(1, self.months + 1)),
            # Operaciones
            'cobros_clientes': [0.0] * self.months,
            'pagos_proveedores': [0.0] * self.months,
            'pagos_gastos_fijos': [0.0] * self.months,
            'pagos_nominas': [0.0] * self.months,
            'pagos_ss': [0.0] * self.months,
            'pagos_intereses': [0.0] * self.months,  # Intereses préstamos + póliza (como en Excel)
            'pagos_irpf': [0.0] * self.months,
            'pagos_iva': [0.0] * self.months,
            'pagos_is': [0.0] * self.months,
            'cf_operaciones': [0.0] * self.months,
            # Inversiones
            'pagos_inversiones': [0.0] * self.months,
            'cf_inversiones': [0.0] * self.months,
            # Financiación
            'entrada_capital': self.df_financiacion['entrada_capital'].values.copy(),
            'entrada_prestamos': self.df_financiacion['entrada_prestamos'].values.copy(),
            'cobros_subvenciones': [0.0] * self.months,
            'pagos_prestamos': [0.0] * self.months,
            'cf_financiacion': [0.0] * self.months,
            # Totales
            'cf_neto': [0.0] * self.months,
            'cf_acumulado': [0.0] * self.months,
            'poliza_credito': [0.0] * self.months,
            'tesoreria_disponible': [0.0] * self.months,
        }

        # Cobros de clientes (ventas + IVA)
        for i in range(self.months):
            data['cobros_clientes'][i] = (self.df_ventas['ventas_totales'][i] +
                                          self.df_ventas['iva_repercutido'][i])

        # Pagos a proveedores (costes variables + IVA compras)
        for i in range(self.months):
            cv = self.df_ventas['costes_variables'][i]
            iva_cv = cv * self.tax_config.iva_compras
            data['pagos_proveedores'][i] = cv + iva_cv

        # Pagos gastos fijos (incluye IVA)
        for i in range(self.months):
            data['pagos_gastos_fijos'][i] = (self.df_gastos['gastos_fijos_totales'][i] +
                                             self.df_gastos['iva_soportado_gastos'][i])

        # Pagos nóminas (sueldo bruto - retenciones trabajador)
        for i in range(self.months):
            data['pagos_nominas'][i] = (self.df_nominas['sueldos_brutos'][i] -
                                        self.df_nominas['ss_trabajador'][i] -
                                        self.df_nominas['irpf'][i])

        # Pagos SS (mes siguiente)
        for i in range(1, self.months):
            data['pagos_ss'][i] = (self.df_nominas['ss_empresa'][i-1] +
                                   self.df_nominas['ss_trabajador'][i-1])

        # Pagos IRPF (mes siguiente)
        for i in range(1, self.months):
            data['pagos_irpf'][i] = self.df_nominas['irpf'][i-1]

        # Pagos IVA: inversiones del mes 0 se recuperan directamente en mes 1;
        # el IVA operativo se liquida con 1 mes de retraso (como en el Excel)
        iva_inv_mes0 = sum(inv.iva for inv in self.inversiones if inv.mes_adquisicion == 1)

        iva_neto_mensual = [0.0] * self.months
        for i in range(self.months):
            iva_rep = self.df_ventas['iva_repercutido'][i]
            iva_inv = self.df_amortizaciones['iva_soportado_inversiones'][i]
            if i == 0:
                iva_inv -= iva_inv_mes0  # Ya gestionado directamente en mes 1
            iva_sop = (self.df_gastos['iva_soportado_gastos'][i] +
                      iva_inv +
                      self.df_ventas['costes_variables'][i] * self.tax_config.iva_compras)
            iva_neto_mensual[i] = iva_rep - iva_sop

        # Guardar IVA neto mensual para usarlo en el balance (acreedores/deudores)
        self.iva_neto_mensual = iva_neto_mensual

        # Mes 1: recuperación directa del IVA de inversiones del mes 0
        data['pagos_iva'][0] = -iva_inv_mes0
        # Meses siguientes: liquidación con 1 mes de retraso
        for i in range(1, self.months):
            data['pagos_iva'][i] = iva_neto_mensual[i - 1]

        # Pagos IS: 1 mes de retraso ("del mes anterior"), como indica el Excel.
        # El P&L ya aplica el crédito fiscal, así que pagamos el IS ajustado del mes anterior.
        for i in range(1, self.months):
            is_mes_anterior = self.cuenta_resultados['impuesto_sociedades'][i - 1]
            if is_mes_anterior > 0:
                data['pagos_is'][i] = is_mes_anterior

        # Pagos inversiones (las del mes 1 ya se pagaron en el mes 0, saldo inicial)
        for inv in self.inversiones:
            if inv.mes_adquisicion > 1 and inv.mes_adquisicion <= self.months:
                data['pagos_inversiones'][inv.mes_adquisicion - 1] += inv.total_con_iva

        # Cobros subvenciones: todas las inversiones en su mes (incluyendo mes 1)
        for inv in self.inversiones:
            if inv.subvencion > 0 and inv.mes_adquisicion <= self.months:
                data['cobros_subvenciones'][inv.mes_adquisicion - 1] += inv.subvencion
        for proy in self.proyectos_trabajo:
            if proy.subvencion > 0 and proy.mes_fin_proyecto <= self.months:
                data['cobros_subvenciones'][proy.mes_fin_proyecto - 1] += proy.subvencion

        # Pagos préstamos (capital)
        data['pagos_prestamos'] = self.df_financiacion['pago_capital_prestamos'].values.copy()

        # Pagos intereses (préstamos + póliza de crédito) - en CF Operaciones como en el Excel
        for i in range(self.months):
            intereses_poliza_mes = self.intereses_poliza[i] if hasattr(self, 'intereses_poliza') else 0
            data['pagos_intereses'][i] = (self.df_financiacion['pago_intereses'][i] +
                                          intereses_poliza_mes)

        # Calcular flujos
        # El saldo inicial (mes 0) incluye capital + préstamos del mes 1
        cf_acum = getattr(self, 'saldo_inicial_tesoreria', 0.0)
        for i in range(self.months):
            # CF Operaciones (incluye intereses como en el Excel row 37)
            data['cf_operaciones'][i] = (data['cobros_clientes'][i] -
                                         data['pagos_proveedores'][i] -
                                         data['pagos_gastos_fijos'][i] -
                                         data['pagos_nominas'][i] -
                                         data['pagos_ss'][i] -
                                         data['pagos_intereses'][i] -
                                         data['pagos_irpf'][i] -
                                         data['pagos_iva'][i] -
                                         data['pagos_is'][i])

            # CF Inversiones
            data['cf_inversiones'][i] = -data['pagos_inversiones'][i]

            # CF Financiación (solo movimientos de capital, sin intereses)
            data['cf_financiacion'][i] = (data['entrada_capital'][i] +
                                          data['entrada_prestamos'][i] +
                                          data['cobros_subvenciones'][i] -
                                          data['pagos_prestamos'][i])

            # CF Neto
            data['cf_neto'][i] = (data['cf_operaciones'][i] +
                                  data['cf_inversiones'][i] +
                                  data['cf_financiacion'][i])

            # CF Acumulado
            cf_acum += data['cf_neto'][i]
            data['cf_acumulado'][i] = cf_acum

            # Póliza de crédito si hay déficit
            if cf_acum < 0:
                data['poliza_credito'][i] = abs(cf_acum)

            # Tesorería disponible
            data['tesoreria_disponible'][i] = cf_acum + data['poliza_credito'][i]

        self.flujo_tesoreria = pd.DataFrame(data)
        return self.flujo_tesoreria

    def calculate_balance(self) -> pd.DataFrame:
        """
        Calcula el balance de situación
        """
        if self.flujo_tesoreria is None:
            self.calculate_flujo_tesoreria()

        data = {
            'mes': list(range(1, self.months + 1)),
            # Activo no corriente
            'inmovilizado': self.df_amortizaciones['inmovilizado_neto'].values.copy(),
            'activo_no_corriente': [0.0] * self.months,
            # Activo corriente
            'tesoreria': self.flujo_tesoreria['tesoreria_disponible'].values.copy(),
            'activo_corriente': [0.0] * self.months,
            'activo_total': [0.0] * self.months,
            # Patrimonio neto
            'capital': [0.0] * self.months,
            'resultado_acumulado': [0.0] * self.months,
            'subvenciones_capital': [0.0] * self.months,
            'patrimonio_neto': [0.0] * self.months,
            # Pasivo no corriente
            'deuda_largo_plazo': self.df_financiacion['deuda_largo_plazo'].values.copy(),
            'pasivo_no_corriente': [0.0] * self.months,
            # Pasivo corriente
            'deuda_corto_plazo': self.df_financiacion['deuda_corto_plazo'].values.copy(),
            'poliza_credito': self.flujo_tesoreria['poliza_credito'].values.copy(),
            'pasivo_corriente': [0.0] * self.months,
            'pasivo_total': [0.0] * self.months,
            'pn_pasivo_total': [0.0] * self.months,
            'check_balance': [0.0] * self.months,
        }

        capital_acum = self.capital_inicial
        for i in range(self.months):
            # Acumular entradas de capital (ampliaciones)
            capital_acum += self.df_financiacion['entrada_capital'][i]
            data['capital'][i] = capital_acum

            # Resultado acumulado
            data['resultado_acumulado'][i] = self.cuenta_resultados['resultado_acumulado'][i]

            # Subvenciones de capital: total subvenciones - amortización acumulada de subvenciones
            total_subvenciones = sum(inv.subvencion for inv in self.inversiones)
            total_subvenciones += sum(p.subvencion for p in self.proyectos_trabajo)
            imputacion_acumulada = sum(self.cuenta_resultados['imputacion_subvenciones'][0:i+1])
            data['subvenciones_capital'][i] = total_subvenciones - imputacion_acumulada

            # Crédito fiscal IS pendiente de utilizar ("Realizable de IS" en el Excel)
            # Solo aparece en el activo (deferred tax asset)
            is_credito = getattr(self, '_credito_fiscal_pl', [0.0] * self.months)[i]
            # IS payable: IS del mes actual, se pagará el mes siguiente (1-mes de retraso en CF)
            # Corresponde a "Hacienda pública acreedora por IS" en el Excel
            is_payable = self.cuenta_resultados['impuesto_sociedades'][i]

            # Acreedores a corto plazo: SS, IRPF e IVA del mes actual pendientes de liquidar
            ss_acr = (self.df_nominas['ss_empresa'][i] + self.df_nominas['ss_trabajador'][i])
            irpf_acr = self.df_nominas['irpf'][i]
            iva_neto = getattr(self, 'iva_neto_mensual', [0.0] * self.months)[i]
            iva_acreedora = max(0.0, iva_neto)   # Hacienda acreedora (IVA a pagar)
            iva_deudora = max(0.0, -iva_neto)    # Hacienda deudora IVA (a cobrar, va a AC)

            # Calcular totales
            data['activo_no_corriente'][i] = data['inmovilizado'][i]
            # Activo: tesorería + crédito fiscal IS (Realizable de IS) + IVA deudora
            data['activo_corriente'][i] = data['tesoreria'][i] + is_credito + iva_deudora
            data['activo_total'][i] = data['activo_no_corriente'][i] + data['activo_corriente'][i]

            data['patrimonio_neto'][i] = (data['capital'][i] + data['resultado_acumulado'][i] +
                                          data['subvenciones_capital'][i])

            data['pasivo_no_corriente'][i] = data['deuda_largo_plazo'][i]
            # Pasivo corriente: deudas CP + póliza + crédito fiscal IS (simétrico al activo)
            # + IS payable del mes actual (Hacienda acreedora IS, se paga el mes siguiente)
            # + SS, IRPF, IVA del mes actual
            data['pasivo_corriente'][i] = (data['deuda_corto_plazo'][i] +
                                           data['poliza_credito'][i] + is_credito + is_payable +
                                           ss_acr + irpf_acr + iva_acreedora)
            data['pasivo_total'][i] = data['pasivo_no_corriente'][i] + data['pasivo_corriente'][i]

            data['pn_pasivo_total'][i] = data['patrimonio_neto'][i] + data['pasivo_total'][i]

            # Check: Activo = PN + Pasivo
            data['check_balance'][i] = data['activo_total'][i] - data['pn_pasivo_total'][i]

        self.balance = pd.DataFrame(data)
        return self.balance

    def calculate_ratios(self) -> Dict[str, Any]:
        """
        Calcula ratios financieros clave
        """
        if self.balance is None:
            self.calculate_balance()

        ratios = {
            'por_ano': {},
            'globales': {}
        }

        for ano in range(1, self.years + 1):
            mes_fin = ano * 12
            if mes_fin > self.months:
                break

            idx = mes_fin - 1  # Índice del último mes del año

            # Datos del año
            inicio_idx = (ano - 1) * 12
            ventas_ano = sum(self.cuenta_resultados['ingresos'][inicio_idx:mes_fin])
            resultado_ano = sum(self.cuenta_resultados['resultado'][inicio_idx:mes_fin])
            ebitda_ano = sum(self.cuenta_resultados['ebitda'][inicio_idx:mes_fin])

            activo = self.balance['activo_total'][idx]
            pasivo = self.balance['pasivo_total'][idx]
            pn = self.balance['patrimonio_neto'][idx]
            activo_corriente = self.balance['activo_corriente'][idx]
            pasivo_corriente = self.balance['pasivo_corriente'][idx]

            ratios['por_ano'][ano] = {
                # Márgenes
                'margen_ebitda': ebitda_ano / ventas_ano if ventas_ano > 0 else 0,
                'margen_beneficio': resultado_ano / ventas_ano if ventas_ano > 0 else 0,

                # Rentabilidad
                'roe': resultado_ano / pn if pn > 0 else 0,  # Return on Equity
                'roa': resultado_ano / activo if activo > 0 else 0,  # Return on Assets

                # Liquidez
                'ratio_liquidez': activo_corriente / pasivo_corriente if pasivo_corriente > 0 else float('inf'),

                # Solvencia
                'ratio_solvencia': activo / pasivo if pasivo > 0 else float('inf'),
                'endeudamiento': pasivo / (pn + pasivo) if (pn + pasivo) > 0 else 0,

                # Fondo de maniobra
                'fondo_maniobra': activo_corriente - pasivo_corriente,
            }

        # Calcular punto de equilibrio (break-even)
        if self.lineas_venta and self.cuenta_resultados is not None:
            # Costes fijos anuales (año 1)
            costes_fijos_ano1 = sum(self.cuenta_resultados['gastos_fijos_servicios'][0:12])
            costes_fijos_ano1 += sum(self.cuenta_resultados['gastos_nomina'][0:12])
            costes_fijos_ano1 += sum(self.cuenta_resultados['amortizaciones'][0:12])

            # Margen de contribución medio
            ventas_ano1 = sum(self.cuenta_resultados['ingresos'][0:12])
            cv_ano1 = sum(self.cuenta_resultados['costes_variables'][0:12])
            margen_contribucion = (ventas_ano1 - cv_ano1) / ventas_ano1 if ventas_ano1 > 0 else 0

            if margen_contribucion > 0:
                punto_equilibrio_euros = costes_fijos_ano1 / margen_contribucion
                ratios['globales']['punto_equilibrio_euros'] = punto_equilibrio_euros

                # Mes en que se alcanza el punto de equilibrio
                ventas_acum = 0
                mes_be = None
                for i in range(self.months):
                    ventas_acum += self.cuenta_resultados['ingresos'][i]
                    if ventas_acum >= punto_equilibrio_euros:
                        mes_be = i + 1
                        break
                ratios['globales']['mes_punto_equilibrio'] = mes_be

        # Necesidad de refinanciación
        max_deficit = 0
        mes_max_deficit = None
        for i in range(self.months):
            if self.flujo_tesoreria['cf_acumulado'][i] < max_deficit:
                max_deficit = self.flujo_tesoreria['cf_acumulado'][i]
                mes_max_deficit = i + 1

        ratios['globales']['deficit_maximo'] = abs(max_deficit)
        ratios['globales']['mes_deficit_maximo'] = mes_max_deficit
        ratios['globales']['necesita_poliza'] = max_deficit < 0

        self.ratios = ratios
        return self.ratios

    def generate_all_projections(self) -> Dict[str, Any]:
        """
        Genera todas las proyecciones financieras
        """
        self.cuenta_resultados = self.calculate_cuenta_resultados()
        self.flujo_tesoreria = self.calculate_flujo_tesoreria()
        self.balance = self.calculate_balance()
        self.ratios = self.calculate_ratios()

        # Calcular componentes de Año 0 para display
        inv_mes1 = sum(inv.total_con_iva for inv in self.inversiones if inv.mes_adquisicion == 1)
        inv_mes1_base = sum(inv.importe for inv in self.inversiones if inv.mes_adquisicion == 1)
        sub_mes1 = sum(inv.subvencion for inv in self.inversiones if inv.mes_adquisicion == 1 and inv.subvencion > 0)

        return {
            'cuenta_resultados': self.cuenta_resultados,
            'flujo_tesoreria': self.flujo_tesoreria,
            'balance': self.balance,
            'ratios': self.ratios,
            'saldo_inicial_tesoreria': getattr(self, 'saldo_inicial_tesoreria', 0.0),
            'capital_inicial': self.capital_inicial,
            'inversiones_mes1': inv_mes1,
            'inversiones_mes1_base': inv_mes1_base,
            'subvenciones_mes1': sub_mes1,
        }

    def get_resumen_anual(self) -> pd.DataFrame:
        """
        Genera un resumen anual de los principales indicadores
        """
        if self.cuenta_resultados is None:
            self.generate_all_projections()

        data = {
            'ano': list(range(1, self.years + 1)),
            'ingresos': [],
            'ingresos_trabajo_propio_activo': [],
            'costes_variables': [],
            'margen_comercial': [],
            'gastos_fijos': [],
            'ebitda': [],
            'imputacion_subvenciones': [],
            'resultado': [],
            'cf_neto': [],
            'tesoreria_final': [],
        }

        for ano in range(1, self.years + 1):
            inicio = (ano - 1) * 12
            fin = ano * 12

            data['ingresos'].append(sum(self.cuenta_resultados['ingresos'][inicio:fin]))
            data['ingresos_trabajo_propio_activo'].append(sum(self.cuenta_resultados['ingresos_trabajo_propio_activo'][inicio:fin]))
            data['costes_variables'].append(sum(self.cuenta_resultados['costes_variables'][inicio:fin]))
            data['margen_comercial'].append(sum(self.cuenta_resultados['margen_comercial'][inicio:fin]))
            gastos = sum(self.cuenta_resultados['gastos_fijos_servicios'][inicio:fin])
            gastos += sum(self.cuenta_resultados['gastos_nomina'][inicio:fin])
            data['gastos_fijos'].append(gastos)
            data['ebitda'].append(sum(self.cuenta_resultados['ebitda'][inicio:fin]))
            data['imputacion_subvenciones'].append(sum(self.cuenta_resultados['imputacion_subvenciones'][inicio:fin]))
            data['resultado'].append(sum(self.cuenta_resultados['resultado'][inicio:fin]))
            data['cf_neto'].append(sum(self.flujo_tesoreria['cf_neto'][inicio:fin]))
            data['tesoreria_final'].append(self.flujo_tesoreria['tesoreria_disponible'][fin - 1])

        return pd.DataFrame(data)
