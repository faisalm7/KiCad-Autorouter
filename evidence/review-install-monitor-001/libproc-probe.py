import ctypes,json,os,subprocess,sys,time
lib=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
lib.proc_listpgrppids.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_int];lib.proc_listpgrppids.restype=ctypes.c_int
lib.proc_pidinfo.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int];lib.proc_pidinfo.restype=ctypes.c_int
p=subprocess.Popen([sys.executable,'-c','import time; data=bytearray(8*1024*1024); time.sleep(1)'],start_new_session=True)
try:
 time.sleep(.15);ids=(ctypes.c_int*32)();count=lib.proc_listpgrppids(p.pid,ids,ctypes.sizeof(ids));infos=[]
 for pid in list(ids)[:count]:
  data=(ctypes.c_uint64*12)();ctypes.set_errno(0);n=lib.proc_pidinfo(pid,4,0,data,ctypes.sizeof(data));infos.append({'pid':pid,'size':n,'errno':ctypes.get_errno(),'rss':data[1]})
 print(json.dumps({'owned_child':p.pid,'count':count,'infos':infos}))
finally:
 p.wait(timeout=3)
