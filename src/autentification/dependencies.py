from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .Segurity import Segurity
from .enums import ExceptionsEnum

security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Ingresa tu token JWT sin el prefijo 'Bearer'"
)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependencia para validar el token JWT y obtener el usuario actual.
    Se integra automáticamente con la documentación de Swagger.
    """
    segurity_instance = Segurity()
    
    if not segurity_instance.validateToken(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ExceptionsEnum.NO_TOKEN.value,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"token": credentials.credentials}