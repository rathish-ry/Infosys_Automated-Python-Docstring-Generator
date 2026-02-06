"""Module for data processing operations."""


class DataProcessor:
    """Handles data processing operations."""

    def load_data(self, filepath):
        """Load data from file."""
        with open(filepath, 'r') as f:
            return f.read()

    def clean_data(self, data):
        """Clean the input data."""
        return data.strip()

    def validate_data(self, data):
        return len(data) > 0


def transform_data(raw_data):
    return raw_data.upper()


def save_data(data, output_path):
    with open(output_path, 'w') as f:
        f.write(data)
