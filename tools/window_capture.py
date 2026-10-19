import ctypes as C
import ctypes.util
from PIL import Image
class XImage(C.Structure):
 _fields_=[('width',C.c_int),('height',C.c_int),('xoffset',C.c_int),('format',C.c_int),
           ('data',C.c_void_p),('byte_order',C.c_int),('bitmap_unit',C.c_int),
           ('bitmap_bit_order',C.c_int),('bitmap_pad',C.c_int),('depth',C.c_int),
           ('bytes_per_line',C.c_int),('bits_per_pixel',C.c_int),('red_mask',C.c_ulong),
           ('green_mask',C.c_ulong),('blue_mask',C.c_ulong)]
def capture_x11(xid,path):
 lib=C.CDLL(ctypes.util.find_library('X11'))
 lib.XOpenDisplay.argtypes=[C.c_char_p];lib.XOpenDisplay.restype=C.c_void_p
 lib.XGetGeometry.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.POINTER(C.c_uint)]
 lib.XGetImage.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_ulong,C.c_int];lib.XGetImage.restype=C.POINTER(XImage)
 lib.XDestroyImage.argtypes=[C.POINTER(XImage)]
 lib.XCloseDisplay.argtypes=[C.c_void_p]
 display=lib.XOpenDisplay(None)
 if not display:raise RuntimeError('X11 display is unavailable')
 try:
  root=C.c_ulong();x=C.c_int();y=C.c_int();width=C.c_uint();height=C.c_uint();border=C.c_uint();depth=C.c_uint()
  if not lib.XGetGeometry(display,xid,C.byref(root),C.byref(x),C.byref(y),C.byref(width),C.byref(height),C.byref(border),C.byref(depth)):raise RuntimeError('Cannot read window geometry')
  handle=lib.XGetImage(display,xid,0,0,width.value,height.value,C.c_ulong(-1).value,2)
  if not handle:raise RuntimeError('Cannot capture window')
  try:
   frame=handle.contents
   assert frame.bits_per_pixel==32 and frame.byte_order==0 and frame.depth==32
   data=C.string_at(frame.data,frame.bytes_per_line*frame.height)
   image=Image.frombytes('RGBa',(frame.width,frame.height),data,'raw','BGRa',frame.bytes_per_line).convert('RGBA')
   image.save(path)
  finally:lib.XDestroyImage(handle)
 finally:lib.XCloseDisplay(display)
