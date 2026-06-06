from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
<<<<<<< HEAD

=======
>>>>>>> 7be98a4 (feat: add screenplay schema design and JSON/YAML definitions)
