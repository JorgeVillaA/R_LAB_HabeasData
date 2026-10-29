"""Lectura de secretos desde el Administrador de credenciales de Windows (lineamiento R-04, locker por aplicativo).

El client_secret de la API real de Zeus vive SOLO ahí: nunca en código, configuración, variables del robot, logs ni
fixtures. En configuración solo se declara el NOMBRE (target) de la credencial, que no es un secreto.
Sin dependencias: usa advapi32 (CredReadW) por ctypes. Fuera de Windows devuelve None.
"""
import ctypes
import sys
from ctypes import wintypes

CRED_TYPE_GENERIC = 1


class _FILETIME(ctypes.Structure):
    _fields_ = [("bajo", wintypes.DWORD), ("alto", wintypes.DWORD)]


class _CREDENCIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR), ("LastWritten", _FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
    ]


def leer_secreto(target):
    """Secreto de la credencial genérica `target`, o None si no existe (o no es Windows)."""
    if sys.platform != "win32" or not target:
        return None
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.POINTER(ctypes.POINTER(_CREDENCIAL))]
    advapi.CredReadW.restype = wintypes.BOOL
    advapi.CredFree.argtypes = [ctypes.c_void_p]
    puntero = ctypes.POINTER(_CREDENCIAL)()
    if not advapi.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(puntero)):
        return None
    try:
        credencial = puntero.contents
        crudo = ctypes.string_at(credencial.CredentialBlob, credencial.CredentialBlobSize)
    finally:
        advapi.CredFree(puntero)
    secreto = crudo.decode("utf-16-le", errors="ignore")
    return secreto or None
