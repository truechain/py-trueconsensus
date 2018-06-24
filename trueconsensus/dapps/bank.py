# import sqlite3
import pickle

from trueconsensus.proto import proto_message as message
from trueconsensus.fastchain.config import config_general
from trueconsensus.fastchain.config import client_logger
from datetime import datetime


class bank:
    def __init__(self, _id, number):
        self.accounts = {}
        self.number = number
        self.id = _id
        self.total_tx = 0
        self.transaction_history = {}
        for i in range(number):
            self.accounts[i] = 100
    # for now assume message is:
    # [_type][ammount][dest]
    #   4       4      4
    # all in ascii because faster to code
    # TODO: make this its own protobuff _type
    def process_request(self, key, _id, seq, req):
        self.transaction_history[seq] = req
        self.total_tx += 1
        #print "EXECUTED TX #", self.total_tx
        msg = req.inner.msg
        src = req.inner.id
        _type = msg[:4]
        if _type != "TRAN":
            m = message.add_sig(key, _id, seq, req.inner.view, "RESP", "INVALID", req.inner.timestamp)
            return m

        ammount = int(msg[4:8])
        dest = int(msg[8:12])

        if _type == "TRAN":
            if ammount > self.accounts[src]:
                m = message.add_sig(
                    key, 
                    _id, 
                    seq, 
                    req.inner.view, 
                    "RESP", 
                    bytes("INVALID", encoding="utf-8"), 
                    req.inner.timestamp
                )
                #print "transfer request invalid"
                return m
            else:
                self.accounts[src] = self.accounts[src] - ammount
                self.accounts[dest] = self.accounts[dest] + ammount
                m = message.add_sig(
                    key, 
                    id, 
                    seq, 
                    req.inner.view, 
                    "RESP",bytes("APPROVED", encoding="utf-8"), 
                    req.inner.timestamp
                )
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


def retrieve_ledger(node_id):
    ledger_loc = os.path.join(
        config_general.get('node', 'ledger_location'),
        'ledger_for_node_%d.db' % node_id
    )
    return ledger_loc

def open_db_conn(node_id):
    try:
        # conn = sqlite3.connect(bank_ledger_loc)
        # c = conn.cursor()
        db = open(retrieve_ledger(node_id), 'wb')
        # db = pickledb.load(, False) 
    except Exception as E:
        import pdb; pdb.set_trace()

    client_logger.debug("Opened Database connection..")
    return db

def load_db_data(node_id):
    db = open(retrieve_ledger(node_id), 'rb')
    data = pickle.load(db)
    return data

def close_db_conn(node_id, db):
    try:
        # db.commit()
        # db.close()
        db.close()
        # write back to ledger
    except Exception as E:
        import pdb; pdb.set_trace()

    client_logger.debug("Closed Database connection..")
    return

def write_to_db(data, db):
    pickle.dump(data, db)

def gen_accounts(n, c):
    client_logger.debug("Generating %d accounts" % n)
    try:
        # c.execute('''CREATE TABLE customers
        #             (date text, name text, fiat real)''')
        for i in range(n):
            # TODO: add to log ledger, the txn info 
            # c.execute("INSERT INTO customers VALUES ('%s','%s', %d)" % (
            #     datetime.now().strftime("%Y-%m-%d"), 
            #     "cust_id_%d" % i,
            #     random.randint(1, 1000)
            # )
            pass
    except Exception as E:
        import pdb; pdb.set_trace()

    client_logger.debug("Generating %d accounts" % n)

def query_acc(_id, c):
    pass