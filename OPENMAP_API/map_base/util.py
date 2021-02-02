from random import randint

def generate_uid_node_map():
    mac = [ randint(0,255) for x in range(6) ]
    mac[0] = (mac[0] & 0xf0) | 0x03
    node_str = ''.join( ['{0:02x}'.format(x) for x in mac] )
    return node_str

def generate_uid_node_campaign():
    mac = [ randint(0,255) for x in range(6) ]
    mac[0] = (mac[0] & 0xf0) | 0x07
    node_str = ''.join( ['{0:02x}'.format(x) for x in mac] )
    return node_str

def generate_uid_node_experiment():
    mac = [ randint(0,255) for x in range(6) ]
    mac[0] = (mac[0] & 0xf0) | 0x0b
    node_str = ''.join( ['{0:02x}'.format(x) for x in mac] )
    return node_str
