

class GraftService(object):
    def __init__(self):
        pass

    @staticmethod
    def validate(transaction):
        return True

    @staticmethod
    def sign(transaction):
        return transaction, "sign_{}".format(transaction)
