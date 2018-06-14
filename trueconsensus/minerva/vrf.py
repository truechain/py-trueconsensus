from fastchain.config import IP_LIST, config_yaml


class VariableDayLengthFrequency(object):
    '''
    VRF function that chooses a set of nodes from the given IP_LIST pool of addresses
    '''
    # TODO: IP_LIST should actually follow the hash address convention
    # of ethereum n/w config pool
    def __init__(self):
        self.snailpool = []
        self.bftpool = []
        self.recentp = []
        self.slow_csize = config_yaml['slowchain']['csize']
        self.fast_csize = config_yaml['bft_committee']['csize']
        
