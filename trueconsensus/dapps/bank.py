from proto import proto_message as message
from fastchain.config import config_general


class bank:
    def __init__(self,id,number):
        self.accounts = {}
        self.number = number
        self.id = id
        self.total_tx = 0
        self.transaction_history = {}
        for i in range(number):
            self.accounts[i] = 100
    # for now assume message is:
    # [type][ammount][dest]
    #   4       4      4
    # all in ascii because faster to code
    # TODO: make this its own protobuff type
    def process_request(self,key,id,seq,req):
        self.transaction_history[seq] = req
        self.total_tx += 1
        #print "EXECUTED TX #", self.total_tx
        msg = req.inner.msg
        src = req.inner.id
        type = msg[:4]
        if type != "TRAN":
            m = message.add_sig(key, id, seq, req.inner.view, "RESP", "INVALID", req.inner.timestamp)
            return m

        ammount = int(msg[4:8])
        dest = int(msg[8:12])

        if type == "TRAN":
            if ammount > self.accounts[src]:
                m = message.add_sig(key, id, seq, req.inner.view, "RESP", "INVALID", req.inner.timestamp)
                #print "transfer request invalid"
                return m
            else:
                self.accounts[src] = self.accounts[src] - ammount
                self.accounts[dest] = self.accounts[dest] + ammount
                m = message.add_sig(key, id, seq, req.inner.view, "RESP", "APPROVED", req.inner.timestamp)
                #print "transfer request approved"
                return m

    def print_balances(self):
        acc_ledger_loc = os.path.join(
            config_general.get('node', 'ledger_location'),
            "bank%s.txt" % self.id)
        f = open(acc_ledger_loc, 'w')
        for i in range(self.number):
            f.write("Account: " + str(i) + "\tBalance: " + str(self.accounts[i]) + "\n")
        f.close()

        txn_ledger_loc = os.path.join(
            config_general.get('node', 'ledger_location'),
            "tx%s.txt" % self.id)
        f = open(txn_ledger_loc, 'w')
        f.write("TOTAL TX: " + str(self.total_tx) + "\n")
        for seq,req in self.transaction_history.iteritems():
            f.write(str(seq) + "\t" + req.inner.msg + "\n")
        f.close()
