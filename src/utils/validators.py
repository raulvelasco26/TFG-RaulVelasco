"""
Funciones de validación de datos para el PEF
"""

def validate_positive_number(value, field_name="valor"):
    """
    Valida que un valor sea un número positivo

    Args:
        value: Valor a validar
        field_name: Nombre del campo para mensajes de error

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        num = float(value)
        if num < 0:
            return False, f"{field_name} debe ser un número positivo"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} debe ser un número válido"


def validate_percentage(value, field_name="porcentaje"):
    """
    Valida que un valor sea un porcentaje válido (0-100)

    Args:
        value: Valor a validar
        field_name: Nombre del campo

    Returns:
        tuple: (is_valid, error_message)
    """
    is_valid, error = validate_positive_number(value, field_name)
    if not is_valid:
        return is_valid, error

    num = float(value)
    if num > 100:
        return False, f"{field_name} no puede ser mayor a 100%"

    return True, None


def validate_investment_financing_balance(inversiones_total, financiacion_total):
    """
    Valida que la financiación cubra las inversiones

    Args:
        inversiones_total: Total de inversiones
        financiacion_total: Total de financiación

    Returns:
        tuple: (is_valid, warning_message)
    """
    if financiacion_total < inversiones_total:
        deficit = inversiones_total - financiacion_total
        return False, f"La financiación es insuficiente. Faltan {deficit:.2f}"

    if financiacion_total > inversiones_total * 1.5:
        exceso = financiacion_total - inversiones_total
        return True, f"Hay un exceso de financiación de {exceso:.2f}. ¿Es correcto?"

    return True, None


# TODO: Implementar más validaciones según se desarrolle el proyecto
