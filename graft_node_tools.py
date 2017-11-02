import os


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
GRAFT_NETWORK_ROOT = os.path.join(APP_ROOT, "..", "GraftNetwork")
GRAFT_NETWORK_BIN = os.path.join(GRAFT_NETWORK_ROOT, 'build', 'release', 'bin')
GRAFT_WALLET_RPC_LOGIN = "monero-wallet-rpc.28982.login"
WALLETS_PATH = os.path.join(GRAFT_NETWORK_BIN, 'wallets')


def get_wallet_rpc_credentials():
    return None, None
