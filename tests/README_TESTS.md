# Suite de Tests - PEF AI Assistant

## Descripción

Esta suite verifica que el motor financiero reproduce fielmente los cálculos del template Excel PEF ToolBoard v2.0. Hay tres tipos de tests:

- **Tests unitarios**: lógica interna de clases y cálculos aislados
- **Tests de regresión (golden)**: el motor produce los mismos valores que el Excel de referencia
- **Tests de casos límite (edge cases)**: comportamientos en los bordes del horizonte de 60 meses

## Archivos

| Archivo | Tests | Descripción |
|---|---|---|
| `test_financial_engine.py` | 56 | Tests unitarios de `Inversion`, `Prestamo` y clases base |
| `test_excel_comparison.py` | 44 | Tests unitarios de componentes del motor (P&L, CF, Balance) |
| `test_validators.py` | 9 | Tests de validación de inputs |
| `test_golden.py` | 6 | Regresión contra `fixtures/pef_test.xlsx` |
| `test_edge_cases.py` | 13 | Casos límite con datos sintéticos |

**Total: 128 tests — todos pasan ✅**

## Ejecución

```bash
# Todos los tests
python -m pytest tests/ -v

# Solo regresión + edge cases (los más relevantes para el motor)
python -m pytest tests/test_golden.py tests/test_edge_cases.py -v

# Un módulo concreto
python -m pytest tests/test_excel_comparison.py::TestAmortizacionInversiones -v

# Con cobertura
python -m pytest tests/ --cov=src/components --cov-report=html
```

## Tests de Regresión (`test_golden.py`)

Carga `fixtures/pef_test.xlsx` con `read_template`, ejecuta el motor y compara contra valores verificados manualmente en Excel. Tolerancia: ±1€.

| Test | Qué verifica |
|---|---|
| `test_amortizaciones_anuales` | Amortizaciones años 1–5 coinciden con Excel |
| `test_imputacion_subvenciones_anuales` | Imputación de subvenciones años 1–5 |
| `test_cf_neto_anual` | CF neto anual años 1–5 |
| `test_cobros_subvenciones_tpa_en_ano2` | La subvención TPA se cobra en año 2 (mes 13), nunca en año 1 |
| `test_total_activo_anual` | Activo total fin de año 1–5 |
| `test_balance_cuadra_todos_los_anos` | Activo = PN + Pasivo en todos los años |

## Tests de Casos Límite (`test_edge_cases.py`)

Construyen engines ad-hoc con datos sintéticos. No necesitan el Excel.

### Motor vacío
- El motor no falla sin ningún dato de entrada
- El balance cuadra incluso sin operaciones

### Subvención TPA (timing crítico)
- `mes_fin=60`: el cobro caería en mes 61 (fuera del horizonte) → no aparece en CF
- `mes_fin=59`: el cobro es en mes 60 (último mes) → sí aparece
- `mes_fin=12`: el cobro es en mes 13 → pertenece al año 2, no al año 1

### Amortización de inversiones adicionales
- Inversión en mes 59: solo amortiza 1 mes dentro del horizonte
- CAPEX inicial (mes_adq=1): amortiza desde mes 1 inclusive
- Inversión adicional (mes_adq>1): el mes de adquisición NO amortiza, el siguiente sí

### Umbrales IRPF
- Salario < 15.000€ → tramo bajo (0% por defecto)
- 15.000€ ≤ salario < 90.000€ → tramo medio (20%)
- Salario ≥ 90.000€ → tramo alto (40%)

### Préstamos
- Préstamo al 0%: total devuelto = importe exacto
- Período de carencia: solo intereses, capital = 0

## Infraestructura de Tests

### `engine_factory.py`
Construye un `FinancialEngine` a partir de un `dict` con la misma estructura que `st.session_state`, sin dependencia de Streamlit. Permite usar el motor en tests.

### `conftest.py`
Fixture `golden_results` con scope de sesión: carga el Excel de referencia una sola vez y devuelve resúmenes anuales de P&L, CF y Balance.

### `fixtures/pef_test.xlsx`
Excel de referencia generado con la aplicación. Contiene datos de prueba con inversiones, TPA, préstamos e ingresos para ejercitar los cálculos más complejos.

## Convenciones de Timing (replicadas del Excel)

| Concepto | Regla |
|---|---|
| Amortización CAPEX inicial (mes_adq=1) | Empieza en el mismo mes de adquisición |
| Amortización inversión adicional (mes_adq>1) | Empieza el mes siguiente al de adquisición |
| Cobro subvención TPA | En `mes_fin_proyecto + 1` |
| Primer pago de préstamo | Un mes después del inicio |
| Liquidación IVA | A mes vencido |
| Pago SS e IRPF | Mes siguiente al devengo |

## Mantenimiento

Actualizar cuando:
- Se modifique `financial_engine.py` con cambios en la lógica de cálculo
- Cambien reglas fiscales o contables en la metodología PEF
- Se genere un nuevo Excel de referencia con datos más representativos (reemplazar `fixtures/pef_test.xlsx` y actualizar los valores en `test_golden.py`)
