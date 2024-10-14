import requests
import json

labr_token_balance = None
wtrx_token_balance = None
wtrx_price_in_usd = None
latest_labr_price = None

def fetch_data() -> None:
    global latest_labr_price
    def fetch_balances() -> None:
        global labr_token_balance
        global wtrx_token_balance

        response_in_json = json.loads(requests.get('''https://apilist.tronscanapi.com/api/account/tokens?address=TV2R7Hh1p3tbrJXhLJcYwMg3LZ7PNxRZGN&start=0&limit=20&hidden=0&show=0&sortType=0&sortBy=0&token=''').text)
        
        for token in response_in_json['data']:
            if token['tokenAbbr'] == 'LABR':
                labr_token_balance = token['quantity']
            elif token['tokenAbbr'] == 'WTRX':
                wtrx_token_balance = token['quantity']

    def fetch_price() -> None:
        global wtrx_price_in_usd
        
        response_in_json = json.loads(requests.get('''https://apilist.tronscanapi.com/api/token_trc20?contract=TNUC9Qb1rRpS5CbWLmNMxXBjyFoydXjWFR&showAll=1&start=&limit=1''').text)
        
        wtrx_price_in_usd = response_in_json['trc20_tokens'][0]['market_info']['priceInUsd']

    fetch_balances()
    fetch_price()
    latest_labr_price = wtrx_token_balance / labr_token_balance * wtrx_price_in_usd

    if labr_token_balance is None or wtrx_token_balance is None or wtrx_price_in_usd is None:
        print('Error while fetching data. Try again later.')
        exit(-1)

def calculate_slippage(token_x_balance: int, token_y_balance: int, delta_x: int, delta_y: int) -> float:
    return (delta_x / delta_y) - (token_x_balance / token_y_balance)

def calculate_price_after_buying(token_x_balance: int, token_y_balance: int, delta_x: int) -> float:
    delta_y = (delta_x * token_y_balance) / (token_x_balance + delta_x)
    slippage = calculate_slippage(token_x_balance, token_y_balance, delta_x, delta_y)
    new_token_x_balance = token_x_balance + delta_x
    new_token_y_balance = token_y_balance - delta_y

    return (new_token_x_balance / new_token_y_balance) * (1 + slippage)

def calculate_price_after_selling(token_x_balance: int, token_y_balance: int, delta_y: int) -> float:
    delta_x = (delta_y * token_x_balance) / (token_y_balance + delta_y)
    slippage = calculate_slippage(token_x_balance, token_y_balance, delta_x, delta_y)
    new_token_x_balance = token_x_balance - delta_x
    new_token_y_balance = token_y_balance + delta_y
    return (new_token_x_balance / new_token_y_balance) * (1 - slippage)

def main():
    tx_type_choice = int(input('Choose the transaction type: Selling (0) / Buying (1)\n'))

    if tx_type_choice == 0:
        labr_amount = int(input('Enter the amount in LABR:'))
        new_labr_price = calculate_price_after_selling(wtrx_token_balance, labr_token_balance, labr_amount) * wtrx_price_in_usd
        print(f'Price after selling: {new_labr_price:.6f}$')
        print(f'Price would change by {(new_labr_price - latest_labr_price):.6f}$ ({((new_labr_price - latest_labr_price) / latest_labr_price * 100):.1f}%)')
    elif tx_type_choice == 1:
        currency_choice = int(input('Choose the currency: USD (0) / TRX (1)\n'))
        if currency_choice == 0:
            amount_in_usd = int(input('Enter the amount in USD:'))
            amount_in_wtrx = amount_in_usd / wtrx_price_in_usd
        elif currency_choice == 1:
            amount_in_wtrx = int(input('Enter the amount in TRX:'))
        else:
            print('Wrong choice. Try again.')
            exit(-1)
        new_labr_price = calculate_price_after_buying(wtrx_token_balance, labr_token_balance, amount_in_wtrx) * wtrx_price_in_usd
        print(f'Price after buying: {new_labr_price:.6f}$')
        print(f'Price would change by {(new_labr_price - latest_labr_price):.6f}$ ({((new_labr_price - latest_labr_price) / latest_labr_price * 100):.1f}%)')
    else:
        print('Wrong choice. Try again.')
        exit(-1)
        

if __name__ == '__main__':
    fetch_data()
    print(f'Current LABR price: {latest_labr_price:.6f}$')
    main()
