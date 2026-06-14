"""
Factoría del FinancialEngine desacoplada de Streamlit.

Acepta un dict con la misma estructura que st.session_state y devuelve
un FinancialEngine listo para calcular. Permite usarlo en tests sin UI.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from components.financial_engine import FinancialEngine


def build_engine(ss: dict) -> FinancialEngine:
    """Construye y configura un FinancialEngine a partir de un dict de sesión.

    Args:
        ss: dict con la misma estructura que st.session_state de la app.

    Returns:
        FinancialEngine configurado y listo para llamar a generate_all_projections().
    """
    engine = FinancialEngine()

    # Configuración fiscal
    fiscal = ss.get("fiscalidad", {})
    engine.set_tax_config(
        is_rate=fiscal.get("is_rate", 25.0) / 100,
        iva_ventas=fiscal.get("iva_ventas", 21.0) / 100,
        iva_compras=fiscal.get("iva_compras", 21.0) / 100,
        iva_inversiones=fiscal.get("iva_inversiones", 21.0) / 100,
        ss_autonomos_rate=fiscal.get("ss_autonomos_rate", 15.0) / 100,
        ss_empresa_rate=fiscal.get("ss_empresa_rate", 33.0) / 100,
        ss_trabajador_rate=fiscal.get("ss_trabajador_rate", 6.5) / 100,
        ss_tope_autonomos=fiscal.get("ss_tope_autonomos", 56640.0),
        ss_tope_general=fiscal.get("ss_tope_general", 56640.0),
        irpf_bajo=fiscal.get("irpf_bajo", 0.0) / 100,
        irpf_medio=fiscal.get("irpf_medio", 20.0) / 100,
        irpf_alto=fiscal.get("irpf_alto", 40.0) / 100,
    )

    iva_inv = fiscal.get("iva_inversiones", 21.0) / 100
    capex_iva_cero = {"terrenos", "fianzas"}
    capex_no_amortizable = {"fianzas"}  # Fianzas: depósito a valor completo, sin amortización

    capex_mapping = {
        "investigacion": "Investigación y desarrollo",
        "patentes": "Patentes y marcas",
        "aplicaciones": "Aplicaciones informáticas",
        "otros_intangibles": "Otros intangibles",
        "terrenos": "Terrenos y construcciones",
        "instalaciones": "Instalaciones",
        "maquinaria": "Maquinaria",
        "equipos": "Equipos informáticos",
        "mobiliario": "Mobiliario",
        "vehiculos": "Vehículos",
        "otros_materiales": "Otros materiales",
        "fianzas": "Fianzas y depósitos",
    }

    # 1. CAPEX
    inversiones = []
    for key, nombre in capex_mapping.items():
        data = ss.get("capex", {}).get(key, {})
        importe = data.get("importe", 0)
        if importe > 0:
            inversiones.append({
                "concepto": nombre,
                "importe": importe,
                "vida_util_anos": 0 if key in capex_no_amortizable else data.get("anos", 5),
                "mes_adquisicion": 1,
                "subvencion": data.get("subvencion", 0),
                "iva_rate": 0.0 if key in capex_iva_cero else iva_inv,
            })

    for key, pi in ss.get("proyectos_inversion", {}).items():
        if pi.get("importe", 0) > 0:
            inversiones.append({
                "concepto": pi.get("observaciones", key) or key,
                "importe": pi["importe"],
                "vida_util_anos": pi.get("anos", 5),
                "mes_adquisicion": pi.get("mes_adquisicion", 13),
                "subvencion": pi.get("subvencion", 0),
                "iva_rate": iva_inv,
            })

    engine.set_inversiones(inversiones)

    # 2. Proyectos de trabajo activo propio
    proyectos_trabajo = []
    for key, pt in ss.get("proyectos_trabajo", {}).items():
        if pt.get("importe", 0) > 0:
            proyectos_trabajo.append({
                "concepto": pt.get("observaciones", key) or key,
                "importe": pt["importe"],
                "vida_util_anos": pt.get("anos", 5),
                "mes_inicio_proyecto": pt.get("mes_inicio", 1),
                "mes_fin_proyecto": pt.get("mes_fin", 12),
                "subvencion": pt.get("subvencion", 0),
            })
    engine.set_proyectos_trabajo(proyectos_trabajo)

    # 3. Financiación
    financiacion_data = ss.get("financiacion", {})
    prestamos = []

    if financiacion_data.get("prestamo1", {}).get("importe", 0) > 0:
        p1 = financiacion_data["prestamo1"]
        prestamos.append({
            "nombre": "Préstamo 1",
            "importe": p1["importe"],
            "mes_inicio": p1.get("mes_inicio", 1),
            "meses_carencia": p1.get("meses_carencia", 0),
            "meses_amortizacion": p1.get("meses_amortizacion", 60),
            "interes_anual": p1.get("interes", 5.0) / 100,
        })

    if financiacion_data.get("prestamo2", {}).get("importe", 0) > 0:
        p2 = financiacion_data["prestamo2"]
        prestamos.append({
            "nombre": "Préstamo 2",
            "importe": p2["importe"],
            "mes_inicio": p2.get("mes_inicio", 1),
            "meses_carencia": p2.get("meses_carencia", 0),
            "meses_amortizacion": p2.get("meses_amortizacion", 60),
            "interes_anual": p2.get("interes", 0.0) / 100,
        })

    cap_ini = financiacion_data.get("capital_inicial", {})
    capital_inicial_total = cap_ini.get("importe", 0) if isinstance(cap_ini, dict) else cap_ini

    ampliacion_data = financiacion_data.get("ampliacion", {})
    ampliaciones = []
    if isinstance(ampliacion_data, dict) and ampliacion_data.get("importe", 0) > 0:
        ampliaciones.append({"mes": ampliacion_data.get("mes", 21), "importe": ampliacion_data["importe"]})

    engine.set_financiacion({
        "capital_inicial": capital_inicial_total,
        "ampliaciones": ampliaciones,
        "poliza_interes": financiacion_data.get("poliza_interes", 3.0) / 100,
        "prestamos": prestamos,
    })

    # 4. OPEX gastos fijos
    gastos_fijos = []
    opex_data = ss.get("opex", {}).get("gastos_fijos", {})
    gastos_mapping = {
        "alquileres": "Alquileres",
        "suministros": "Suministros",
        "rentings": "Rentings",
        "reparaciones": "Reparaciones",
        "servicios_prof": "Servicios profesionales",
        "transportes": "Transportes",
        "bancarios_seguros": "Gastos bancarios y seguros",
        "marketing": "Marketing",
        "tributos": "Tributos municipales",
    }
    for key, nombre in gastos_mapping.items():
        data = opex_data.get(key, {})
        ano1 = data.get("ano1", 0)
        if ano1 > 0:
            incrementos = data.get("incrementos", [0.0, 0.0, 0.0, 0.0])
            importes = [float(ano1)]
            for inc in incrementos:
                importes.append(importes[-1] * (1 + inc / 100))
            gastos_fijos.append({
                "concepto": nombre,
                "importes_anuales": importes,
                "iva_rate": fiscal.get("iva_compras", 21.0) / 100,
            })

    # 5. Empleados
    empleados = []
    incrementos_salariales = {}
    perfiles_config = {
        "socios": ("Socios fundadores", True),
        "perfil_a": ("Personal tipo A", False),
        "perfil_b": ("Personal tipo B", False),
        "perfil_c": ("Personal tipo C", False),
        "perfil_d": ("Personal tipo D", False),
    }

    emp_data = ss.get("empleados_data", {})
    if emp_data:
        keys = list(emp_data.keys())
        if isinstance(keys[0], int) and "perfiles" in emp_data.get(1, {}):
            for etapa_num in [1, 2, 3]:
                if etapa_num in emp_data:
                    incrementos_salariales[etapa_num] = emp_data[etapa_num].get("incremento_salario", 0) / 100
                    for key, (nombre, es_autonomo) in perfiles_config.items():
                        data = emp_data[etapa_num].get("perfiles", {}).get(key, {})
                        if data.get("num", 0) > 0:
                            empleados.append({
                                "perfil": f"{nombre} (Etapa {etapa_num})",
                                "num_trabajadores": data["num"],
                                "mes_alta": data.get("alta", 1),
                                "mes_baja": data.get("baja", 60),
                                "sueldo_bruto_anual": data.get("salario", 0),
                                "es_autonomo": es_autonomo,
                                "etapa": etapa_num,
                            })
        elif isinstance(keys[0], int):
            for etapa_num in [1, 2, 3]:
                if etapa_num in emp_data:
                    for key, (nombre, es_autonomo) in perfiles_config.items():
                        data = emp_data[etapa_num].get(key, {})
                        if data.get("num", 0) > 0:
                            empleados.append({
                                "perfil": f"{nombre} (Etapa {etapa_num})",
                                "num_trabajadores": data["num"],
                                "mes_alta": data.get("alta", 1),
                                "mes_baja": data.get("baja", 60),
                                "sueldo_bruto_anual": data.get("salario", 0),
                                "es_autonomo": es_autonomo,
                                "etapa": etapa_num,
                            })
        else:
            for key, (nombre, es_autonomo) in perfiles_config.items():
                data = emp_data.get(key, {})
                if data.get("num", 0) > 0:
                    empleados.append({
                        "perfil": nombre,
                        "num_trabajadores": data["num"],
                        "mes_alta": data.get("alta", 1),
                        "mes_baja": data.get("baja", 60),
                        "sueldo_bruto_anual": data.get("salario", 0),
                        "es_autonomo": es_autonomo,
                        "etapa": 1,
                    })

    engine.incrementos_salariales = incrementos_salariales
    engine.set_gastos_operativos(gastos_fijos, empleados)

    # 6. Ingresos
    lineas = []
    for tipo_key in ["tipo_a", "tipo_b", "tipo_c"]:
        data = ss.get("ingresos", {}).get(tipo_key, {})
        sam = data.get("sam", 0)
        precio = data.get("precio", 0)
        if sam > 0 and precio > 0:
            som_list = [s / 100 if s > 0 else 0 for s in data.get("som", [0, 0, 0, 0, 0])]
            inc_list = [0] + [i / 100 for i in data.get("incremento", [0, 0, 0, 0])]
            lineas.append({
                "nombre": data.get("nombre", tipo_key),
                "sam": sam,
                "som_anual": som_list,
                "precio_inicial": precio,
                "incremento_precio_anual": inc_list,
                "cv_produccion": data.get("cv_produccion", 0) / 100,
                "cv_adquisicion": data.get("cv_adquisicion", 0) / 100,
                "comisiones": data.get("comisiones", 0) / 100,
            })
    engine.set_ingresos(lineas)

    return engine
