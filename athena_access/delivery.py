"""Injectable SMTP delivery using a fixed public origin."""
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlsplit


def smtp_delivery(config):
    origin = config['ATHENA_PUBLIC_ORIGIN'].rstrip('/')
    parsed = urlsplit(origin)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment):
        raise ValueError('ATHENA_PUBLIC_ORIGIN deve ser a origem HTTPS pública do portal.')
    host = config['ATHENA_SMTP_HOST']
    sender = config['ATHENA_SMTP_FROM']
    port = int(config.get('ATHENA_SMTP_PORT', 587))

    def send(email, path):
        message = EmailMessage()
        message['From'] = sender
        message['To'] = email
        message['Subject'] = 'Recuperação de senha'
        message.set_content(f'Para definir uma nova senha, abra o link em até 30 minutos:\n{origin}{path}\n')
        context = ssl.create_default_context()
        factory = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
        options = {'context': context} if port == 465 else {}
        with factory(host, port, timeout=8, **options) as server:
            if port != 465:
                server.starttls(context=context)
            if config.get('ATHENA_SMTP_USER'):
                server.login(config['ATHENA_SMTP_USER'], config['ATHENA_SMTP_PASSWORD'])
            server.send_message(message)
    return send
