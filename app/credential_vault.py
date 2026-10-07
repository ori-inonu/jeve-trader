"""Current user's Windows Credential Manager. No plaintext file fallback."""
import ctypes
from ctypes import wintypes
import sys


class WindowsCredentialVault:
    def __init__(self, target='JeveTrader/TypeSafe/JEV'):
        self.target = target

    def _api(self):
        if sys.platform != 'win32':
            raise OSError('Gerenciador de Credenciais requer Windows')
        class Credential(ctypes.Structure):
            _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD), ('TargetName', wintypes.LPWSTR),
                        ('Comment', wintypes.LPWSTR), ('LastWritten', wintypes.FILETIME),
                        ('CredentialBlobSize', wintypes.DWORD), ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
                        ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
                        ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]
        api = ctypes.WinDLL('Advapi32', use_last_error=True)
        pointer = ctypes.POINTER(Credential)
        api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(pointer)]
        api.CredReadW.restype = wintypes.BOOL
        api.CredWriteW.argtypes = [pointer, wintypes.DWORD]
        api.CredWriteW.restype = wintypes.BOOL
        api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        api.CredDeleteW.restype = wintypes.BOOL
        api.CredFree.argtypes = [ctypes.c_void_p]
        return api, Credential

    def read(self):
        api, Credential = self._api()
        pointer = ctypes.POINTER(Credential)()
        if not api.CredReadW(self.target, 1, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == 1168:
                return ''
            raise OSError('Não foi possível ler a credencial protegida')
        try:
            return ctypes.string_at(pointer.contents.CredentialBlob, pointer.contents.CredentialBlobSize).decode('utf-8')
        finally:
            api.CredFree(pointer)

    def write(self, key):
        if not isinstance(key, str) or not 1 <= len(key) <= 2560 or any(not 33 <= ord(c) <= 126 for c in key):
            raise ValueError('Chave inválida')
        api, Credential = self._api()
        blob = (ctypes.c_ubyte * len(key))(*key.encode('ascii'))
        credential = Credential(Type=1, TargetName=self.target, CredentialBlobSize=len(blob), CredentialBlob=blob,
                                Persist=2, UserName='Jeve Trader')
        try:
            if not api.CredWriteW(ctypes.byref(credential), 0):
                raise OSError('Não foi possível salvar a credencial protegida')
        finally:
            ctypes.memset(blob, 0, len(blob))

    def delete(self):
        api, _ = self._api()
        if not api.CredDeleteW(self.target, 1, 0) and ctypes.get_last_error() != 1168:
            raise OSError('Não foi possível remover a credencial protegida')
