import requests
from django.conf import settings

def send_telegram_message(order):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    # Формируем текст сообщения
    items_text = '\n'.join([f'{item.name} x {item.quantity} = {item.total} Br' for item in order.items.all()])
    message = (
        f"🆕 *Новый заказ #{order.id}*\n\n"
        f"👤 *Клиент:* {order.first_name} {order.last_name}\n"
        f"📞 *Телефон:* {order.phone}\n"
        f"📧 *Email:* {order.email or 'не указан'}\n"
        f"🏠 *Адрес:* {order.address}\n"
        f"💬 *Комментарий:* {order.comment or 'нет'}\n\n"
        f"🛒 *Товары:*\n{items_text}\n\n"
        f"💰 *Итого:* {order.total_price} Br"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        return response.ok
    except Exception:
        return False