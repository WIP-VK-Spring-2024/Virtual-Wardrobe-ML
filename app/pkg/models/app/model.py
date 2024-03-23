"""Models of model task object."""

import uuid

from pydantic import PositiveInt
from pydantic.fields import Field
from pydantic import UUID4

from app.pkg.models.base import BaseModel as Model
from app.pkg.models.app.image_type import ImageType
from app.pkg.settings import settings

__all__ = [
    "CreateTaskCmd",
    "CreateTaskFileCmd",
    "CreateRespFileCmd",
]


class BaseModel(Model):
    """Base model for user."""


class ModelFields:
    """Model fields of user."""

    user_id: UUID4 = Field(description="User id.", example=uuid.uuid4)
    clothes_id: UUID4 = Field(description="Clothes id.", example=uuid.uuid4)
    image_type: ImageType = Field(
        description="Image type.",
        example=ImageType.CLOTH,
    )
    message: str = Field(description="Message.", example="Successfully uploaded.")
    file_name: str = Field(description="File name.")
    file_path: str = Field(
        description="file path.",
        default=str(settings.API_FILESYSTEM_FOLDER),
    )


class CreateTaskCmd(BaseModel):
    clothes_id: UUID4 = ModelFields.clothes_id
    user_id: UUID4 = ModelFields.user_id

    person_file_name: str = ModelFields.file_name


class CreateTaskFileCmd(CreateTaskCmd):
    person_file_path: str = ModelFields.file_path
    
    clothes_file_name: str = ModelFields.file_name
    clothes_file_path: str = ModelFields.file_path

class CreateRespFileCmd(BaseModel):
    clothes_id: UUID4 = ModelFields.clothes_id
    user_id: UUID4 = ModelFields.user_id
    res_file_name: str = ModelFields.file_name
    res_file_path: str = ModelFields.file_path


class ResponseMessage(BaseModel):
    message: str = ModelFields.message