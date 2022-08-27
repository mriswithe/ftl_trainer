from ctypes import wintypes
import ctypes
import win32ui
import win32process
import win32api

PROCESS_ALL_ACCESS = 0x1F0FFF
HWND = win32ui.FindWindow(None, "FTL: Faster Than Light").GetSafeHwnd()
PID = win32process.GetWindowThreadProcessId(HWND)[1]

read_process_memory = ctypes.WinDLL("kernel32", use_last_error=True).ReadProcessMemory
read_process_memory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
read_process_memory.restype = wintypes.BOOL
write_process_memory = ctypes.WinDLL("kernel32", use_last_error=True).WriteProcessMemory
write_process_memory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
write_process_memory.restype = wintypes.BOOL

ADDRESS1 = 0x17C8AB3C
ADDRESS2 = ctypes.create_string_buffer(4)
bytes_read = ctypes.c_size_t()
PROCESS = win32api.OpenProcess(PROCESS_ALL_ACCESS, 0, PID)
print(
    read_process_memory(PROCESS.handle, ADDRESS1, ADDRESS2, 4, ctypes.byref(bytes_read))
)

out = ADDRESS2.value
