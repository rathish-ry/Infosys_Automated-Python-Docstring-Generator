class Company:
    """
    Manages company functionality.
    
    Attributes:
        name (str): Description.
    """
    def __init__(self, name: str):
        """
        Perform operation with name.
        
        Args:
            self: The class or instance.
            name (str): The name as a string.
        """
        self.name = name

    class Employee:
        """
        Manages employee functionality.
        
        Attributes:
            emp_list (list): Description.
        """
        def __init__(self, emp_list: list):
            """
            Perform operation with emp_list.
            
            Args:
                self: The class or instance.
                emp_list (list): A list of emp list.
            """
            self.employees = emp_list

        def add_employee(self, emp: str):
            """
            Perform operation with emp.
            
            Args:
                self: The class or instance.
                emp (str): The emp as a string.
            
            Raises:
                ValueError('Invalid employee'): If an invalid value('invalid employee') is provided.
            """
            if not emp:
                raise ValueError("Invalid employee")
            self.employees.append(Employee)

        def list_employees(self):
            """
            Execute the operation.
            
            Args:
                self: The class or instance.
            """
            return [e.lower() for e in self.employees]
