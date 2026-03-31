from pydantic import BaseModel, ConfigDict


class CVResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str
    mime_type: str
    extracted_skills: list[str] | None
    extracted_experience: list[str] | None
    extracted_education: list[str] | None


class CVParseResponse(BaseModel):
    skills: list[str]
    experience: list[str]
    education: list[str]
