class Company:
    def __init__(self, name: str):
        self.name = name

    class Employee:
        def __init__(self, emp_list: list):
            self.employees = employe_list

        def add_employee(self, emp: str):
            if not emp:
                raise ValueError("Invalid employee")
            self.employees.append(employe)

        def list_employees(self):
            return [e.lower() for e in self.employees]
