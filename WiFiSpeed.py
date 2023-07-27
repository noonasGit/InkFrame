import speedtest

def bytes_to_mb(bytes):
  KB = 1024 # One Kilobyte is 1024 bytes
  MB = KB * 1024 # One MB is 1024 KB
  return int(bytes/MB)

wifi  = speedtest.Speedtest()
print("Wifi Download Speed is ", bytes_to_mb(wifi.download()))
print("Wifi Upload Speed is ", bytes_to_mb(wifi.upload()))


