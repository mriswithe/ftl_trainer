import functools
import struct
from abc import abstractmethod
from ctypes import wintypes
import ctypes

import win32api
import win32process
import win32ui

PROCESS_ALL_ACCESS = 0x1F0FFF

_raw_rpm = ctypes.WinDLL("kernel32", use_last_error=True).ReadProcessMemory
_raw_rpm.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
_raw_rpm.restype = wintypes.BOOL
_raw_wpm = ctypes.WinDLL("kernel32", use_last_error=True).WriteProcessMemory
_raw_wpm.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
_raw_wpm.restype = wintypes.BOOL


class InstrumentedValue:
    def __init__(self, offset: int, struct_pattern: str):
        self._offset = offset
        self._size = struct.calcsize(struct_pattern)
        self._pattern = struct_pattern
        self._buffer = ctypes.create_string_buffer(self._size)

    def get(self, handle, base_address):
        bytes_read = ctypes.c_size_t()
        return_code = _raw_rpm(
            handle,
            base_address + self._offset,
            self._buffer,
            self._size,
            ctypes.byref(bytes_read),
        )
        if return_code == 0:
            raise RuntimeError("Shits broke, got 0 from read proc mem")
        return struct.unpack(self._pattern, self._buffer.raw)[0]


class Application:
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def exe_name(self) -> str:
        raise NotImplementedError()

    def __init__(self):
        self._ivs = self._make_properties()
        self.hwnd = win32ui.FindWindow(None, self.name).GetSafeHwnd()
        self.pid = win32process.GetWindowThreadProcessId(self.hwnd)[1]
        self.handle = win32api.OpenProcess(PROCESS_ALL_ACCESS, 0, self.pid)
        self.base_address = self._get_base_address()

    def _make_properties(self):
        ivs = []
        for k, v in self.__dict__.items():
            if isinstance(v, InstrumentedValue):
                ivs.append(v)
            setattr(
                self,
                k,
                property(
                    fget=functools.partial(
                        v.get, handle=self.handle, base_address=self.base_address
                    )
                ),
            )
        return ivs

    def _get_base_address(self):
        modules = win32process.EnumProcessModules(self.handle)
        for module in modules:
            name = win32process.GetModuleFileNameEx(self.handle, module)
            if self.exe_name.lower() in name.lower():
                return module


class FTL(Application):
    name = "FTL: Faster Than Light"
    exe_name = "FTLGame.exe"
    scrap = InstrumentedValue(offset=0x4D4, struct_pattern="i")
