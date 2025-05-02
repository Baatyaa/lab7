import requests
import json
import logging
from datetime import datetime
import os


class AtaixTradeBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.ataix.kz/api"
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })

        # Логирование қосу
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='trade_bot.log'
        )

        # Сақтау бумасын құру
        os.makedirs("sell_orders", exist_ok=True)

    def get_order_status(self, order_id):
        """Ордер статусын тексеру"""
        try:
            response = self.session.get(f"{self.base_url}/orders/{order_id}")
            return response.json()
        except Exception as e:
            logging.error(f"Статус тексеру қатесі: {str(e)}")
            return {"status": False, "error": str(e)}

    def create_sell_order(self, symbol, quantity, buy_price):
        """2% қымбатқа сату ордерін құру"""
        sell_price = round(buy_price * 1.02, 6)  # 2% жоғары
        payload = {
            "symbol": symbol.replace("/", "/"),
            "side": "sell",
            "type": "limit",
            "quantity": str(quantity),
            "price": str(sell_price),
            "subType": "gtc"
        }

        try:
            response = self.session.post(f"{self.base_url}/orders", json=payload)
            return response.json()
        except Exception as e:
            logging.error(f"Ордер құру қатесі: {str(e)}")
            return {"status": False, "error": str(e)}

    def save_to_json(self, order_data, filename_prefix):
        """Ордер ақпаратын JSON файлға сақтау"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sell_orders/{filename_prefix}_{timestamp}.json"

        data_to_save = {
            "order": order_data,
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "price_increase": "2%",
                "original_price": float(order_data['result']['price']) / 1.02,
                "sell_price": float(order_data['result']['price'])
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)

        logging.info(f"Ордер сақталды: {filename}")
        return filename

    def process_filled_order(self, order_id):
        """Filled ордерді өңдеу және 2% қымбатқа сату"""
        # 1. Ордер ақпаратын алу
        order_info = self.get_order_status(order_id)
        if not order_info.get('status'):
            return order_info

        # 2. Тек filled ордерлерді өңдеу
        if order_info['result'].get('status').lower() != 'filled':
            return {
                "status": False,
                "message": f"Ордер әлі орындалмаған. Ағымдағы статус: {order_info['result'].get('status')}"
            }

        # 3. Сату ордерін құру (2% жоғары)
        symbol = order_info['result']['symbol']
        quantity = float(order_info['result']['cumQuantity'])
        buy_price = float(order_info['result']['averagePrice'])

        sell_order = self.create_sell_order(symbol, quantity, buy_price)

        # 4. Нәтижені сақтау
        if sell_order.get('status'):
            saved_file = self.save_to_json(sell_order, f"sell_{order_id}")
            return {
                "success": True,
                "message": "Сату ордері сәтті құрылды",
                "sell_order_id": sell_order['result']['orderID'],
                "buy_order_id": order_id,
                "buy_price": buy_price,
                "sell_price": round(buy_price * 1.02, 6),
                "saved_file": saved_file
            }
        return sell_order


# Мысал қолдану
if __name__ == "__main__":
    # Конфигурация
    API_KEY = "wHxKGrbUdTRvHLT4Ldjho0PpOCqFEc6bW8tWstnSLAfJi0uu7aZFJWlhzkp2Un43zmgrTp0pVQskg7GKFHJJ4n"
    FILLED_ORDER_ID = "LTC-USDT-65712-1746209681834"  # Орындалған сатып алу ордерінің ID

    # Ботты іске қосу
    bot = AtaixTradeBot(API_KEY)

    # Ордерді өңдеу
    result = bot.process_filled_order(FILLED_ORDER_ID)

    # Нәтижені көрсету
    print(json.dumps(result, indent=2, ensure_ascii=False))