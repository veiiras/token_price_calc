import requests
import json
import gradio as gr

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

def process_transaction(tx_type, currency_choice, amount):
    fetch_data()
    
    if tx_type == 'Selling':
        new_labr_price = calculate_price_after_selling(wtrx_token_balance, labr_token_balance, amount) * wtrx_price_in_usd
        price_change = (new_labr_price - latest_labr_price)
        percentage_change = (price_change / latest_labr_price) * 100
        return f'Price after selling: {new_labr_price:.6f}$\nPrice would change by {price_change:.6f}$ ({percentage_change:.1f}%)'

    elif tx_type == 'Buying':
        if currency_choice == 'USD':
            amount_in_wtrx = amount / wtrx_price_in_usd
        elif currency_choice == 'TRX':
            amount_in_wtrx = amount

        new_labr_price = calculate_price_after_buying(wtrx_token_balance, labr_token_balance, amount_in_wtrx) * wtrx_price_in_usd
        price_change = (new_labr_price - latest_labr_price)
        percentage_change = (price_change / latest_labr_price) * 100
        return f'Price after buying: {new_labr_price:.6f}$\nPrice would change by {price_change:.6f}$ ({percentage_change:.1f}%)'

# Функция для обновления состояния выбора валюты
def update_currency_dropdown(tx_type):
    if tx_type == "Selling":
        return gr.update(visible=True, interactive=False)  # Отключаем поле выбора валюты для продажи
    else:
        return gr.update(visible=True, interactive=True)   # Включаем поле выбора валюты для покупки

# Используем gr.Blocks для создания динамических обновлений
with gr.Blocks() as gr_interface:
    tx_type_dropdown = gr.Dropdown(
        ["Selling", "Buying"], 
        label="Transaction Type", 
        value="Buying"
    )

    currency_dropdown = gr.Dropdown(
        ["USD", "TRX"], 
        label="Currency (for Buying)", 
        value="TRX"
    )

    amount_input = gr.Number(label="Enter Amount")
    output_text = gr.Textbox(label="Output")

    # Добавляем обработчик для изменения состояния выбора валюты
    tx_type_dropdown.change(fn=update_currency_dropdown, inputs=[tx_type_dropdown], outputs=[currency_dropdown])

    # Кнопка для запуска транзакции
    submit_btn = gr.Button("Submit")
    submit_btn.click(fn=process_transaction, inputs=[tx_type_dropdown, currency_dropdown, amount_input], outputs=output_text)

if __name__ == "__main__":
    fetch_data()  # Предварительное извлечение данных
    gr_interface.launch()
