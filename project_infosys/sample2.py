class Student:
    def __init__(self, name):
        self.name = name

    def display_name(self):
        print("Student Name:", self.name)


def greet():
    print("Welcome to Python Programming")


s1 = Student("Rathish")
s1.display_name()