from datetime import date
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, EmailStr

from rich.console import Console

console = Console()

class Department(Enum):
    HR = "HR"
    SALES = "SALES"
    IT = "IT"
    ENGINEERING = "ENGINEERING"

class Employee(BaseModel):
    employee_id: UUID = uuid4()
    name: str
    email: EmailStr
    date_of_birth: date
    salary: float
    department: Department
    elected_benefits: bool


employee_one = Employee(
    name="tony",
    email="tony@example.com",
    date_of_birth="1992-10-28",
    salary=123_000.00,
    department="IT",
    elected_benefits=True,
)

# console.print(employee_one)

new_employee_dict = {
    "name": "tony",
    "email": "tony@example.com",
    "date_of_birth": "1992-10-28",
    "salary": 123_000.00,
    "department": "IT",
    "elected_benefits": True,
 }

employee_two = Employee.model_validate(new_employee_dict)
# console.print(employee_two)


console.print(employee_two.model_dump())
console.print_json(employee_two.model_dump_json())


console.print(Employee.model_json_schema())