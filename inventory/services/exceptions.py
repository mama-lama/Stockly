class InventoryServiceError(Exception):
    pass


class ValidationError(InventoryServiceError):
    pass


class EasyKassaAuthError(InventoryServiceError):
    pass
