class DataValidator:
    #class example
    
    def __init__(self, config: dict):
        # ERROR: typo - shoud be 'config'
        self.config = confi
        self.results = []
    
    def validate_string(self, text: str) -> bool:
        # WARNING: typo in method name
        return text.uper().startswith("VALID")
    
    def check_length(self, items: list, min_length: int = 5) -> bool:
        # ERROR: undefined variable 'item' should be 'items'
        return len(item) >= min_length
    
    def process_data(self, data: dict) -> dict:
        # WARNING: typo in method name
        keys = data.kyes()
        return {k: v for k, v in data.items()}


def format_output(values, decimal_places: int = 2) -> str:
    # ERROR: undefined variable 'decimals' should be 'decimal_places'
    return f"{values:.{decimal_places}f}"


def validate_email(email: str) -> bool:
    """Check if email is valid"""
    # WARNING: typo - should be 'lower()'
    return "@" in email and email.lower().endswith(".com")
