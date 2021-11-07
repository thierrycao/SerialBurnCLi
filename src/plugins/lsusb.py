import usb
from usb.core import USBError

from plugins import logger 

### Some auxiliary functions ###
def _clean_str(s):
    '''
    Filter string to allow only alphanumeric chars and spaces

    @param s: string
    @return: string
    '''

    return ''.join([c for c in s if c.isalnum() or c in {' '}])


def _get_dev_string_info(device):
    '''
    Human readable device's info

    @return: string
    '''

    try:
        str_info = _clean_str(usb.util.get_string(device, 256, 2))
        str_info += ' ' + _clean_str(usb.util.get_string(device, 256, 3))
        return str_info
    except USBError:
        return str_info


def get_usb_devices():
    '''
    Get USB devices

    @return: list of tuples (dev_idVendor, dev_idProduct, dev_name)
    '''

    return [(device.idVendor, device.idProduct, _get_dev_string_info(device)) 
                for device in usb.core.find(find_all=True)
                    if device.idProduct > 2]



def get_usb_devlists():
    all_devs = usb.core.find(find_all=True)
    dev_list = []
    dev_dict = {}
    for d in all_devs:
        key = '{0}{1}'.format(hex(d.idVendor), hex(d.idProduct))
        try:
            dev_u = usb.core.find(idVendor=d.idVendor, idProduct=d.idProduct)
            print(dev_u)
            # dev_u.reset()
            # if dev_u:
            #     # dev_u.set_configuration()  # added this line
            #     cfg = dev_u.get_active_configuration()  # exception: access violation writing 0x0000000000000000
            #     intf = cfg[(0, 0)]
            #     ep = intf[0]

            #     dev_list.append(key)
                
            if key in dev_dict:  # 避免重复加入
                continue

            dev_dict[key] = {'idVendor': d.idVendor, 'idProduct': d.idProduct, 'thread': False}
                
        except Exception as e:
            err_str = str(e)
            print("error!", err_str)
        finally:
            return dev_dict

def get_udisk():
    import os
    if os.name == 'posix':
        return get_udisk_partition()
    else:
        import win32file
        def get_drives():
            drives=[]
            sign=win32file.GetLogicalDrives()
            drive_all=["A:\\","B:\\","C:\\","D:\\","E:\\","F:\\","G:\\","H:\\","I:\\",
                        "J:\\","K:\\","L:\\","M:\\","N:\\","O:\\","P:\\","Q:\\","R:\\",
                        "S:\\","T:\\","U:\\","V:\\","W:\\","X:\\","Y:\\","Z:\\"]
            for i in range(25):
                if (sign & 1<<i):
                    if win32file.GetDriveType(drive_all[i])==3:
                        drives.append(drive_all[i])
            return drives
        def is_udisk(drives):
            udisk = []
            for item in drives:
                try :
                    free_bytes,total_bytes,total_free_bytes=win32file.GetDiskFreeSpaceEx(item)
                    print("total_bytes:", total_bytes/1024/1024/1024)
                    if (total_bytes/1024/1024/1024)<17:
                        udisk.append(item)
                except :
                    break
        drives = is_udisk(get_drives())
        return drives

def get_partition():
    import psutil
    part = psutil.disk_partitions()
    return part

def wait_rotate(header=''):
    import time
    index=["/","─","\\","/"]
    index=[logger.get_purple_text(i) for i in index]
    for i in range(len(index)):
        print("\r" + header + index[i], end="")
        time.sleep(0.2)

# psutil.disk_usage(psutil.disk_partitions()[0].device).total
def get_udisk_partition():
    from psutil import disk_partitions
    dev = {'driver':'','opts':''}
    for item in disk_partitions():
        # if 'removable' in item.opts and 'rw' in item.opts:
        if 'msdos' in item.fstype and 'rw' in item.opts:
            dev['driver'], dev['opts'] = item.mountpoint, item.opts
            # print('Found USB Disk: ', dev['driver'])
            return dev
            break
    # print('Not Found USB Disk')
    return dev
