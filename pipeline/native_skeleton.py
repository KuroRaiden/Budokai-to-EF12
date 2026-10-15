"""Read PSP AMO skeleton records; no game assets or third-party tools included."""
import struct

def skeleton(data):
    origin=data.find(b"#AMG")
    if origin<0:raise ValueError("No PSP skeleton found")
    count,axes=struct.unpack_from("<II",data,origin+16)
    axes+=origin
    names=origin+struct.unpack_from("<I",data,origin+28)[0]
    if count>300 or axes+count*80>len(data) or names+count*32>len(data):raise ValueError("Invalid skeleton bounds")
    result=[]
    for index in range(count):
        offset=axes+index*80
        values=struct.unpack_from("<7f",data,offset)
        pointer=struct.unpack_from("<I",data,offset+64)[0]
        parent=(origin+pointer-axes)//80 if pointer else -1
        if parent==index:parent=-1
        if not -1<=parent<count:raise ValueError("Invalid skeleton parent")
        name=data[names+index*32:names+(index+1)*32].split(b"\0")[0].decode("latin1")
        result.append((name,values[:4],values[4:],parent))
    return result
