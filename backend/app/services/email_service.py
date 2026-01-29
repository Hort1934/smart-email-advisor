import asyncio
import email
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from email.header import decode_header
from email.message import EmailMessage as StdEmailMessage
import aiosmtplib
import aiohttp
import ssl
import imaplib

logger = logging.getLogger(__name__)

@dataclass
class EmailMessage:
    uid: str
    subject: str
    sender: str
    recipient: str
    content: str
    html_content: str
    received_at: datetime
    message_id: str
    folder: str
    is_read: bool
    attachments: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []

class EmailService:
    """Сервіс для роботи з email через IMAP/SMTP"""
    
    def __init__(self):
        self.imap_server = "imap.ukr.net"
        self.imap_port = 993
        self.smtp_server = "smtp.ukr.net" 
        self.smtp_port = 465
        self.email_address = "marchenko1934@ukr.net"
        self.email_password = "wcxQsXh4k5qcgovT"
        self.connection = None
        
    def _clean_header(self, header_value: str) -> str:
        """Очищення заголовків від спецсимволів та кодувань"""
        if not header_value:
            return ""
            
        try:
            # Розкодування заголовків
            decoded_parts = decode_header(header_value)
            cleaned_parts = []
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    # Спробувати різні кодування
                    for enc in [encoding, 'utf-8', 'windows-1252', 'iso-8859-1']:
                        if enc:
                            try:
                                cleaned_parts.append(part.decode(enc))
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                    else:
                        # Якщо нічого не працює, використати latin-1
                        cleaned_parts.append(part.decode('latin-1', errors='ignore'))
                else:
                    cleaned_parts.append(str(part))
            
            result = ''.join(cleaned_parts)
            # Видалення зайвих символів
            result = result.replace('\r', ' ').replace('\n', ' ')
            # Обмеження довжини
            return result[:500] if len(result) > 500 else result
            
        except Exception as e:
            logger.warning(f"Error cleaning header: {e}")
            return str(header_value)[:500]
    
    async def connect(self):
        """Підключення до IMAP серверу"""
        try:
            # Використовуємо синхронний IMAP для простоти
            self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.connection.login(self.email_address, self.email_password)
            logger.info("Successfully connected to email server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False
    
    async def disconnect(self):
        """Відключення від IMAP серверу"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
                
    async def list_folders(self) -> List[str]:
        """Отримання списку доступних папок"""
        if not await self.connect():
            raise Exception("Cannot connect to email server")
            
        try:
            # Отримання списку папок
            result, folders = self.connection.list()
            folder_names = []
            
            for folder in folders:
                # Парсинг назви папки
                folder_info = folder.decode('utf-8')
                # Витягування назви папки після останнього розділювача
                if '"' in folder_info:
                    parts = folder_info.split('"')
                    if len(parts) >= 3:
                        folder_name = parts[-2]
                        folder_names.append(folder_name)
            
            await self.disconnect()
            return folder_names
            
        except Exception as e:
            await self.disconnect()
            logger.error(f"Error listing folders: {e}")
            return ["INBOX", "Sent", "Drafts", "Spam", "Trash"]  # Fallback
    
    async def get_emails_from_folder(self, folder_name: str, limit: int = 10) -> List[EmailMessage]:
        """Отримання листів з конкретної папки"""
        if not await self.connect():
            raise Exception("Cannot connect to email server")
        
        try:
            # Спроба підключитися до папки
            folder_variants = [folder_name, folder_name.upper(), folder_name.lower()]
            
            selected_folder = None
            for variant in folder_variants:
                try:
                    self.connection.select(variant, readonly=True)
                    selected_folder = variant
                    break
                except:
                    continue
            
            if not selected_folder:
                await self.disconnect()
                raise Exception(f"Cannot access folder: {folder_name}")
            
            # Пошук всіх листів
            result, message_ids = self.connection.search(None, 'ALL')
            
            if result != 'OK':
                await self.disconnect()
                return []
            
            # Отримання останніх листів
            message_id_list = message_ids[0].split()
            latest_messages = message_id_list[-limit:] if len(message_id_list) > limit else message_id_list
            
            emails = []
            for msg_id in reversed(latest_messages):  # Від новіших до старіших
                try:
                    email_msg = await self._fetch_email(msg_id.decode())
                    if email_msg:
                        email_msg.folder = folder_name
                        emails.append(email_msg)
                except Exception as e:
                    logger.warning(f"Error fetching email {msg_id}: {e}")
                    continue
            
            await self.disconnect()
            return emails
            
        except Exception as e:
            await self.disconnect()
            logger.error(f"Error getting emails from {folder_name}: {e}")
            return []
    
    async def get_spam_emails(self, limit: int = 10) -> List[EmailMessage]:
        """Отримання листів зі спам папки"""
        # Спроба різних варіантів назви spam папки
        spam_folders = ["Spam", "SPAM", "Junk", "JUNK", "Спам"]
        
        for folder_name in spam_folders:
            try:
                emails = await self.get_emails_from_folder(folder_name, limit)
                if emails:
                    logger.info(f"Found {len(emails)} emails in {folder_name} folder")
                    return emails
            except Exception as e:
                logger.debug(f"Folder {folder_name} not accessible: {e}")
                continue
        
        logger.warning("No accessible spam folder found")
        return []
    
    async def get_inbox_emails(self, limit: int = 10) -> List[EmailMessage]:
        """Отримання листів з вхідних"""
        return await self.get_emails_from_folder("INBOX", limit)
    
    async def _fetch_email(self, message_id: str) -> Optional[EmailMessage]:
        """Отримання конкретного листа за ID"""
        try:
            # Отримання листа
            result, msg_data = self.connection.fetch(message_id, '(RFC822)')
            
            if result != 'OK' or not msg_data or not msg_data[0]:
                return None
            
            # Парсинг email
            email_content = msg_data[0][1]
            msg = email.message_from_bytes(email_content)
            
            # Витягування базової інформації
            subject = self._clean_header(msg.get('Subject', ''))
            sender = self._clean_header(msg.get('From', ''))
            recipient = self._clean_header(msg.get('To', ''))
            message_id_header = msg.get('Message-ID', f'generated-{message_id}')
            
            # Дата отримання
            date_str = msg.get('Date')
            received_at = self._parse_date(date_str)
            
            # Витягування тексту
            content, html_content = await self._extract_email_content(msg)
            
            return EmailMessage(
                uid=message_id,
                subject=subject,
                sender=sender,
                recipient=recipient,
                content=content,
                html_content=html_content,
                received_at=received_at,
                message_id=message_id_header,
                folder="",  # Буде встановлено зовні
                is_read=True,  # За замовчуванням
                attachments=[]
            )
            
        except Exception as e:
            logger.error(f"Error fetching email {message_id}: {e}")
            return None
    
    async def _extract_email_content(self, msg) -> tuple[str, str]:
        """Витягування тексту та HTML з email"""
        text_content = ""
        html_content = ""
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if "attachment" not in content_disposition:
                        if content_type == "text/plain":
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                text_content += part.get_payload(decode=True).decode(charset, errors='ignore')
                            except:
                                text_content += str(part.get_payload())
                        elif content_type == "text/html":
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                html_content += part.get_payload(decode=True).decode(charset, errors='ignore')
                            except:
                                html_content += str(part.get_payload())
            else:
                # Простий текст
                content_type = msg.get_content_type()
                charset = msg.get_content_charset() or 'utf-8'
                
                try:
                    payload = msg.get_payload(decode=True).decode(charset, errors='ignore')
                except:
                    payload = str(msg.get_payload())
                
                if content_type == "text/html":
                    html_content = payload
                else:
                    text_content = payload
            
            # Обрізання контенту якщо занадто довгий
            if len(text_content) > 5000:
                text_content = text_content[:5000] + "... (truncated)"
            if len(html_content) > 10000:
                html_content = html_content[:10000] + "... (truncated)"
                
        except Exception as e:
            logger.warning(f"Error extracting email content: {e}")
            text_content = "Error extracting content"
        
        return text_content, html_content
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг дати з email заголовку"""
        if not date_str:
            return datetime.now(timezone.utc)
        
        try:
            # Використання email.utils для парсингу дати
            from email.utils import parsedate_tz, mktime_tz
            parsed = parsedate_tz(date_str)
            if parsed:
                timestamp = mktime_tz(parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {e}")
        
        return datetime.now(timezone.utc)