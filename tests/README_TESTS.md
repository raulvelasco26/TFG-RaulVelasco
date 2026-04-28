# Suite de Tests Exhaustivos - PEF AI Assistant

## Descripción

Esta suite de tests verifica que el motor financiero de la aplicación Python reproduce fielmente los cálculos del template Excel PEF ToolBoard v2.0.

## Cobertura de Tests

### 1. Tests de Amortización de Inversiones (`test_excel_comparison.py`)
- ✅ Amortización lineal simple
- ✅ Inmovilizado neto que decrece correctamente
- ✅ Múltiples inversiones con diferentes períodos
- ✅ Inversiones adquiridas en meses posteriores
- ✅ IVA soportado en inversiones
- ✅ Imputación de subvenciones proporcional

### 2. Tests de Préstamos y Financiación
- ✅ Cálculo de cuota francesa
- ✅ Período de carencia (solo intereses)
- ✅ Préstamos sin intereses
- ✅ Amortización total correcta
- ✅ Clasificación de deuda en corto y largo plazo

### 3. Tests de Nóminas y Personal
- ✅ Coste empresa en régimen general
- ✅ Coste de autónomos
- ✅ Tope de cotización a la Seguridad Social
- ✅ IRPF por tramos (bajo, medio, alto)
- ✅ Empleados temporales (alta/baja parcial)
- ✅ Múltiples trabajadores del mismo perfil

### 4. Tests de Ingresos y Ventas
- ✅ Ventas con SOM (Share of Market) creciente
- ✅ Incremento de precios año a año
- ✅ Costes variables sobre ventas
- ✅ IVA repercutido

### 5. Tests de Gastos Fijos (OPEX)
- ✅ Gastos sin incremento anual
- ✅ Gastos con incremento compuesto
- ✅ Distribución mensual correcta

### 6. Tests de Cuenta de Resultados (P&L)
- ✅ Cálculo del margen comercial
- ✅ Cálculo del EBITDA
- ✅ Cálculo del EBIT con amortizaciones
- ✅ Impuesto de Sociedades con crédito fiscal (compensación de pérdidas)
- ✅ Resultado acumulado mes a mes

### 7. Tests de Flujo de Caja (Cash Flow)
- ✅ Cobros de clientes incluyen IVA
- ✅ Pagos de IVA a mes vencido
- ✅ Pagos de SS al mes siguiente
- ✅ Pagos de IRPF al mes siguiente
- ✅ Póliza de crédito con déficit
- ✅ Tesorería disponible nunca negativa
- ✅ Cálculo del saldo inicial

### 8. Tests de Balance
- ✅ Ecuación fundamental: Activo = PN + Pasivo
- ✅ Patrimonio neto incluye resultado acumulado
- ✅ Deuda total decrece con amortización

### 9. Tests de Proyectos de Trabajo Propio (I+D)
- ✅ Ingresos durante el proyecto
- ✅ Amortización después de activación

### 10. Tests de Integración Completos
- ✅ Startup sin financiación externa
- ✅ Casos con subvenciones
- ✅ Coherencia entre P&L, CF y Balance

## Ejecución de Tests

### Ejecutar todos los tests
```bash
python -m pytest tests/ -v
```

### Ejecutar solo los tests de comparación con Excel
```bash
python -m pytest tests/test_excel_comparison.py -v
```

### Ejecutar tests de un módulo específico
```bash
# Tests de amortización
python -m pytest tests/test_excel_comparison.py::TestAmortizacionInversiones -v

# Tests de préstamos
python -m pytest tests/test_excel_comparison.py::TestPrestamosYFinanciacion -v

# Tests de nóminas
python -m pytest tests/test_excel_comparison.py::TestNominasYPersonal -v
```

### Ejecutar con reporte de cobertura
```bash
python -m pytest tests/ --cov=src/components --cov-report=html
```

## Resultados

**Total de tests:** 109
**Estado:** ✅ Todos los tests pasan correctamente

### Desglose por archivo:
- `test_excel_comparison.py`: 44 tests ✅
- `test_financial_engine.py`: 56 tests ✅
- `test_validators.py`: 9 tests ✅

## Verificación de Precisión

Los tests verifican:

1. **Precisión numérica:** Tolerancia de ±0.01€ en cálculos financieros
2. **Coherencia:** Los valores fluyen correctamente entre estados financieros
3. **Reglas de negocio:** Implementación correcta de:
   - Sistema de amortización lineal
   - Sistema francés de amortización de préstamos
   - Liquidación fiscal (IVA, SS, IRPF, IS)
   - Compensación de pérdidas (crédito fiscal)
   - Póliza de crédito automática

## Casos de Prueba Clave

### Caso 1: Amortización de Préstamos
```python
# Préstamo de 10,000€ a 12 meses al 12% anual
# Verifica: cuota francesa constante, intereses decrecientes, capital creciente
```

### Caso 2: Crédito Fiscal por Pérdidas
```python
# Empresa con pérdidas iniciales que genera beneficio después
# Verifica: IS = 0 en pérdidas, compensación en beneficios futuros
```

### Caso 3: Balance Equilibrado
```python
# En todos los meses: Activo = Patrimonio Neto + Pasivo
# Tolerancia: ±1€ por redondeos
```

## Mantenimiento

Los tests deben actualizarse cuando:
1. Se modifique el motor financiero (`financial_engine.py`)
2. Cambien las reglas fiscales o contables
3. Se detecten discrepancias con el Excel

## Notas Técnicas

### Convenciones de Timing
- **Préstamos:** Primer pago un mes después del inicio
- **IVA:** Liquidación a mes vencido
- **SS e IRPF:** Pago al mes siguiente
- **IS:** Pago con un mes de retraso
- **Inversiones mes 1:** Se pagan en el período 0 (saldo inicial)

### Tolerancias de Redondeo
- Cálculos mensuales: ±0.01€
- Balance: ±1€ (acumulación de redondeos)
- Totales anuales: ±1€
