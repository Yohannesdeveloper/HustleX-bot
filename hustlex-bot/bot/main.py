# bot/main.py
# States for Telegram Job Posting
JOB_TITLE, JOB_TYPE, WORK_LOCATION, SALARY, DEADLINE, DESCRIPTION, CLIENT_TYPE, JOB_LINK, COMPANY_NAME, VERIFIED, PREVIOUS_JOBS = range(11)
import os
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.error import TelegramError
from urllib.parse import urlparse
import aiohttp
from telegram import Bot
from telegram.ext import ApplicationBuilder









BOT_TOKEN = "8034250378:AAH9wK5c10AC69BerzHz7zriXs3eI6X9B5A"

# Create a Bot instance
bot = Bot(token=BOT_TOKEN)

# Delete any existing webhook
bot.delete_webhook(drop_pending_updates=True)

# Optional: Verify webhook is deleted
print("Webhook deleted. Starting bot...")

# Now build your Application as usual
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Add handlers, etc.
# app.add_handler(...)

# Start polling
app.run_polling()
# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://hustlexeth.netlify.app/")
DATABASE_URL = os.getenv("DATABASE_URL")  # Unused in current code, placeholder for future integration

# Simple in-memory storage for CV data and user preferences (replace with database in production)
user_cvs = {}
user_languages = {}
user_profiles = {}

# Helper function to validate bot token
async def validate_bot_token(token: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        bot_info = await context.bot.get_me()
        logger.info(f"Bot token validated successfully: @{bot_info.username}")
        return True
    except TelegramError as e:
        logger.error(f"Invalid bot token: {e}")
        return False

# Helper function to check bot permissions in the channel
async def check_bot_permissions(context: ContextTypes.DEFAULT_TYPE, channel_id: str) -> bool:
    try:
        bot_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            logger.warning(f"Bot is not an admin in channel {channel_id}")
            return False
        if not bot_member.can_send_messages:
            logger.warning(f"Bot lacks 'Send Messages' permission in channel {channel_id}")
            return False
        logger.info(f"Bot has necessary permissions in channel {channel_id}")
        return True
    except TelegramError as e:
        logger.error(f"Error checking bot permissions in channel {channel_id}: {e}")
        return False

# Helper function to validate channel ID
async def validate_channel_id(context: ContextTypes.DEFAULT_TYPE, channel_id: str) -> bool:
    try:
        chat_info = await context.bot.get_chat(chat_id=channel_id)
        logger.info(f"Channel ID {channel_id} is valid: {chat_info.title}")
        return True
    except TelegramError as e:
        logger.error(f"Invalid channel ID {channel_id}: {e}")
        return False

# Helper function to validate WebApp URL
async def validate_webapp_url(url: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    logger.info(f"WebApp URL {url} is reachable")
                    return True
                else:
                    logger.error(f"WebApp URL {url} returned status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error accessing WebApp URL {url}: {e}")
            return False

# Enhanced Markdown escaping for Telegram MarkdownV2
def escape_markdown_v2(text: str) -> str:
    special_chars = r'([_\*\[\]\(\)~`>\#\+\-=\|\{\}\.\!])'
    return re.sub(special_chars, r'\\\1', str(text))

# ---------------------------
# /start command
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await validate_bot_token(TOKEN, context):
        if update.effective_chat:
            await update.effective_chat.send_message("❌ Error: Invalid bot token. Please contact the bot administrator.")
        logger.error("Cannot send message due to invalid bot token")
        return
    
    user_id = update.effective_user.id
    lang_code = user_languages.get(user_id, 'en')
    
    # Language-specific welcome messages
    welcome_messages = {
        'en': {
            'welcome': "Welcome to HustleX — tap Menu to open.",
            'menu': "Menu"
        },
        'es': {
            'welcome': "Bienvenido a HustleX — toca Menú para abrir.",
            'menu': "Menú"
        },
        'fr': {
            'welcome': "Bienvenue sur HustleX — appuyez sur Menu pour ouvrir.",
            'menu': "Menu"
        },
        'de': {
            'welcome': "Willkommen bei HustleX — tippen Sie auf Menü zum Öffnen.",
            'menu': "Menü"
        },
        'it': {
            'welcome': "Benvenuto su HustleX — tocca Menu per aprire.",
            'menu': "Menu"
        },
        'pt': {
            'welcome': "Bem-vindo ao HustleX — toque em Menu para abrir.",
            'menu': "Menu"
        },
        'am': {
            'welcome': "ወደ HustleX እንኳን ደህና መጡ — ለመክፈት ሜኑን ይንኩ።",
            'menu': "ሜኑ"
        }
    }
    
    messages = welcome_messages.get(lang_code, welcome_messages['en'])
    keyboard = [[InlineKeyboardButton(messages['menu'], callback_data="menu")]]
    
    if update.effective_message:
        await update.effective_message.reply_text(
            messages['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.effective_chat.send_message(
            messages['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ---------------------------
# Utility function for safe message editing
# ---------------------------
async def safe_edit_message(query, text, reply_markup=None, parse_mode=None, context=None):
    """Safely edit a message, fallback to sending new message if edit fails"""
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        # If editing fails, send a new message instead
        if context:
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
        )

# ---------------------------
# Menu callback
# ---------------------------
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    lang_code = user_languages.get(user_id, 'en')
    
    # Language-specific menu messages
    menu_messages = {
        'en': {
            'title': "Choose a tab:",
            'post_telegram': "Post Job in Telegram",
            'post_website': "Post Job via Website",
            'profile': "Profile",
            'applications': "Applications",
            'about': "About HustleX",
            'settings': "Settings",
            'error': "❌ Error: WebApp URL is unreachable. Please try again later or contact support."
        },
        'es': {
            'title': "Elige una pestaña:",
            'post_telegram': "Publicar Trabajo en Telegram",
            'post_website': "Publicar Trabajo vía Sitio Web",
            'profile': "Perfil",
            'applications': "Aplicaciones",
            'about': "Acerca de HustleX",
            'settings': "Configuración",
            'error': "❌ Error: La URL de la aplicación web no es accesible. Por favor, inténtalo de nuevo más tarde o contacta con soporte."
        },
        'fr': {
            'title': "Choisissez un onglet:",
            'post_telegram': "Publier un Emploi sur Telegram",
            'post_website': "Publier un Emploi via le Site Web",
            'profile': "Profil",
            'applications': "Candidatures",
            'about': "À propos de HustleX",
            'settings': "Paramètres",
            'error': "❌ Erreur: L'URL de l'application web est inaccessible. Veuillez réessayer plus tard ou contacter le support."
        },
        'de': {
            'title': "Wählen Sie einen Tab:",
            'post_telegram': "Stelle in Telegram veröffentlichen",
            'post_website': "Stelle über Website veröffentlichen",
            'profile': "Profil",
            'applications': "Bewerbungen",
            'about': "Über HustleX",
            'settings': "Einstellungen",
            'error': "❌ Fehler: WebApp-URL ist nicht erreichbar. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support."
        },
        'it': {
            'title': "Scegli una scheda:",
            'post_telegram': "Pubblica Lavoro su Telegram",
            'post_website': "Pubblica Lavoro via Sito Web",
            'profile': "Profilo",
            'applications': "Candidature",
            'about': "Informazioni su HustleX",
            'settings': "Impostazioni",
            'error': "❌ Errore: L'URL dell'applicazione web non è raggiungibile. Riprova più tardi o contatta il supporto."
        },
        'pt': {
            'title': "Escolha uma aba:",
            'post_telegram': "Publicar Emprego no Telegram",
            'post_website': "Publicar Emprego via Site",
            'profile': "Perfil",
            'applications': "Candidaturas",
            'about': "Sobre o HustleX",
            'settings': "Configurações",
            'error': "❌ Erro: A URL da aplicação web não está acessível. Tente novamente mais tarde ou entre em contato com o suporte."
        },
        'am': {
            'title': "አንድ ትር ይምረጡ:",
            'post_telegram': "ሥራን በቴሌግራም ያስቀምጡ",
            'post_website': "ሥራን በድር ጣቢያ ያስቀምጡ",
            'profile': "መገለጫ",
            'applications': "ማመልከቻዎች",
            'about': "ስለ HustleX",
            'settings': "ቅንብሮች",
            'error': "❌ ስህተት: የድር መተግበሪያ URL አይደርስም። እባክዎ ቆይተው ይሞክሩ ወይም ድጋፍን ያግኙ።"
        }
    }
    
    messages = menu_messages.get(lang_code, menu_messages['en'])
    
    # Validate WebApp URL before showing menu
    if not await validate_webapp_url(WEBAPP_URL):
        try:
            await q.edit_message_text(messages['error'])
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=messages['error']
            )
        return
    
    keyboard = [
        [InlineKeyboardButton(messages['post_telegram'], callback_data="post_job_telegram")],
        [InlineKeyboardButton(messages['post_website'], web_app=WebAppInfo(url=f"{WEBAPP_URL}"))],
        [InlineKeyboardButton(messages['profile'], web_app=WebAppInfo(url=f"{WEBAPP_URL}profile.html"))],
        [InlineKeyboardButton(messages['applications'], callback_data="applications")],
        [InlineKeyboardButton(messages['about'], callback_data="about")],
        [InlineKeyboardButton(messages['settings'], callback_data="settings")],
    ]
    
    await safe_edit_message(q, messages['title'], reply_markup=InlineKeyboardMarkup(keyboard), context=context)

# ---------------------------
# Other tab callbacks
# ---------------------------
async def applications_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Applications: (placeholder)")

async def about_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    about_text = (
        "🚀 *About HustleX*\n\n"
        "Welcome to *HustleX* – where *ambition meets opportunity!* ✨\n\n"
        "At HustleX, we believe talent has *no limits* 🌍. Whether you’re a designer 🎨, "
        "developer 💻, writer ✍️, or digital wizard 🪄, we connect skilled freelancers with "
        "clients who value *quality, creativity, and reliability*.\n\n"
        "*Our mission:* 💪 Elevate projects 📈 Transform careers 🌟\n\n"
        "*Why HustleX?*\n"
        "- *Seamless Experience:* Navigate your freelance journey effortlessly ⚡\n"
        "- *Trusted Connections:* Work with verified clients and freelancers 🤝\n"
        "- *Smart Tools:* Manage profiles, applications, and projects—all in Telegram 📲\n"
        "- *Growth-Focused:* Showcase your skills, build your reputation, and level up 🚀\n\n"
        "Join *HustleX* today and turn your skills into opportunities! 🔥 "
        "Because here, *every hustle counts* 💼💎"
    )
    await q.edit_message_text(about_text, parse_mode="Markdown")

async def settings_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    lang_code = user_languages.get(user_id, 'en')
    
    # Language-specific settings messages
    settings_messages = {
        'en': {
            'title': "⚙️ *Settings*",
            'instruction': "Choose a category to manage your preferences:",
            'languages': "🌍 Languages",
            'account': "👤 Account",
            'cv': "📄 My CV",
            'terms': "📋 Terms and Conditions",
            'back': "⬅️ Back to Menu"
        },
        'es': {
            'title': "⚙️ *Configuración*",
            'instruction': "Elige una categoría para gestionar tus preferencias:",
            'languages': "🌍 Idiomas",
            'account': "👤 Cuenta",
            'cv': "📄 Mi CV",
            'terms': "📋 Términos y Condiciones",
            'back': "⬅️ Volver al Menú"
        },
        'fr': {
            'title': "⚙️ *Paramètres*",
            'instruction': "Choisissez une catégorie pour gérer vos préférences:",
            'languages': "🌍 Langues",
            'account': "👤 Compte",
            'cv': "📄 Mon CV",
            'terms': "📋 Termes et Conditions",
            'back': "⬅️ Retour au Menu"
        },
        'de': {
            'title': "⚙️ *Einstellungen*",
            'instruction': "Wählen Sie eine Kategorie zur Verwaltung Ihrer Einstellungen:",
            'languages': "🌍 Sprachen",
            'account': "👤 Konto",
            'cv': "📄 Mein Lebenslauf",
            'terms': "📋 Geschäftsbedingungen",
            'back': "⬅️ Zurück zum Menü"
        },
        'it': {
            'title': "⚙️ *Impostazioni*",
            'instruction': "Scegli una categoria per gestire le tue preferenze:",
            'languages': "🌍 Lingue",
            'account': "👤 Account",
            'cv': "📄 Il Mio CV",
            'terms': "📋 Termini e Condizioni",
            'back': "⬅️ Torna al Menu"
        },
        'pt': {
            'title': "⚙️ *Configurações*",
            'instruction': "Escolha uma categoria para gerenciar suas preferências:",
            'languages': "🌍 Idiomas",
            'account': "👤 Conta",
            'cv': "📄 Meu CV",
            'terms': "📋 Termos e Condições",
            'back': "⬅️ Voltar ao Menu"
        },
        'am': {
            'title': "⚙️ *ቅንብሮች*",
            'instruction': "የሚመርጡትን ለማስተካከል አንድ ምድብ ይምረጡ:",
            'languages': "🌍 ቋንቋዎች",
            'account': "👤 መለያ",
            'cv': "📄 የእኔ CV",
            'terms': "📋 ውሎች እና ሁኔታዎች",
            'back': "⬅️ ወደ ሜኑ ይመለሱ"
        }
    }
    
    messages = settings_messages.get(lang_code, settings_messages['en'])
    
    keyboard = [
        [InlineKeyboardButton(messages['languages'], callback_data="settings_languages")],
        [InlineKeyboardButton(messages['account'], callback_data="settings_account")],
        [InlineKeyboardButton(messages['cv'], callback_data="settings_cv")],
        [InlineKeyboardButton(messages['terms'], callback_data="settings_terms")],
        [InlineKeyboardButton(messages['back'], callback_data="menu")]
    ]
    
    await safe_edit_message(
        q,
        f"{messages['title']}\n\n{messages['instruction']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

# ---------------------------
# Settings Tab Callbacks
# ---------------------------
async def settings_languages_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    current_lang = user_languages.get(user_id, 'en')
    
    lang_names = {
        'en': '🇺🇸 English',
        'es': '🇪🇸 Español', 
        'fr': '🇫🇷 Français',
        'de': '🇩🇪 Deutsch',
        'it': '🇮🇹 Italiano',
        'pt': '🇵🇹 Português',
        'am': '🇪🇹 አማርኛ (Amharic)'
    }
    
    current_lang_name = lang_names.get(current_lang, 'English')
    
    # Language-specific messages
    messages = {
        'en': {
            'title': "🌍 *Language Settings*",
            'instruction': "Select your preferred language:",
            'current': f"📝 *Current:* {current_lang_name}",
            'tip': "💡 *Tip:* Language changes will apply to all bot messages.",
            'back': "⬅️ Back to Settings"
        },
        'es': {
            'title': "🌍 *Configuración de Idioma*",
            'instruction': "Selecciona tu idioma preferido:",
            'current': f"📝 *Actual:* {current_lang_name}",
            'tip': "💡 *Consejo:* Los cambios de idioma se aplicarán a todos los mensajes del bot.",
            'back': "⬅️ Volver a Configuración"
        },
        'fr': {
            'title': "🌍 *Paramètres de Langue*",
            'instruction': "Sélectionnez votre langue préférée:",
            'current': f"📝 *Actuel:* {current_lang_name}",
            'tip': "💡 *Conseil:* Les changements de langue s'appliqueront à tous les messages du bot.",
            'back': "⬅️ Retour aux Paramètres"
        },
        'de': {
            'title': "🌍 *Spracheinstellungen*",
            'instruction': "Wählen Sie Ihre bevorzugte Sprache:",
            'current': f"📝 *Aktuell:* {current_lang_name}",
            'tip': "💡 *Tipp:* Sprachänderungen gelten für alle Bot-Nachrichten.",
            'back': "⬅️ Zurück zu Einstellungen"
        },
        'it': {
            'title': "🌍 *Impostazioni Lingua*",
            'instruction': "Seleziona la tua lingua preferita:",
            'current': f"📝 *Attuale:* {current_lang_name}",
            'tip': "💡 *Suggerimento:* Le modifiche della lingua si applicheranno a tutti i messaggi del bot.",
            'back': "⬅️ Torna alle Impostazioni"
        },
        'pt': {
            'title': "🌍 *Configurações de Idioma*",
            'instruction': "Selecione seu idioma preferido:",
            'current': f"📝 *Atual:* {current_lang_name}",
            'tip': "💡 *Dica:* As mudanças de idioma se aplicarão a todas as mensagens do bot.",
            'back': "⬅️ Voltar às Configurações"
        },
        'am': {
            'title': "🌍 *የቋንቋ ቅንብሮች*",
            'instruction': "የሚመርጡትን ቋንቋ ይምረጡ:",
            'current': f"📝 *አሁን ያለ:* {current_lang_name}",
            'tip': "💡 *ምክር:* የቋንቋ ለውጦች ለሁሉም የቦት መልዕክቶች ይተገበራሉ።",
            'back': "⬅️ ወደ ቅንብሮች ይመለሱ"
        }
    }
    
    msg = messages.get(current_lang, messages['en'])
    
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
        [InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang_it")],
        [InlineKeyboardButton("🇵🇹 Português", callback_data="lang_pt")],
        [InlineKeyboardButton("🇪🇹 አማርኛ (Amharic)", callback_data="lang_am")],
        [InlineKeyboardButton(msg['back'], callback_data="settings")]
    ]
    
    await safe_edit_message(
        q,
        f"{msg['title']}\n\n{msg['instruction']}\n\n{msg['current']}\n{msg['tip']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

async def settings_account_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("👤 View Profile", callback_data="account_edit_profile")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="account_notifications")],
        [InlineKeyboardButton("🗑️ Delete Account", callback_data="account_delete")],
        [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
    ]
    
    await safe_edit_message(
        q,
        f"👤 *Account Settings*\n\n"
        f"📋 *Profile Information:*\n"
        f"• Name: {user.first_name or 'Not set'}\n"
        f"• Username: @{user.username or 'Not set'}\n"
        f"• User ID: {user.id}\n\n"
        f"⚙️ Manage your account settings below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

async def settings_cv_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    has_cv = user_id in user_cvs and user_cvs[user_id] is not None
    
    if has_cv:
        cv_info = user_cvs[user_id]
        keyboard = [
            [InlineKeyboardButton("👁️ View Current CV", callback_data="cv_view")],
            [InlineKeyboardButton("📤 Upload New CV", callback_data="cv_upload")],
            [InlineKeyboardButton("🗑️ Remove CV", callback_data="cv_remove")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        status_text = f"✅ CV uploaded: {cv_info.get('filename', 'Unknown')}"
    else:
        keyboard = [
            [InlineKeyboardButton("📤 Upload New CV", callback_data="cv_upload")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
        ]
        status_text = "❌ No CV uploaded"
    
    await safe_edit_message(
        q,
        f"📄 *My CV*\n\n"
        f"📁 *Current Status:* {status_text}\n"
        f"📝 *Supported formats:* PDF, DOCX\n"
        f"📏 *Max file size:* 16 MB\n\n"
        f"💡 *Tip:* A well-formatted CV increases your chances of getting hired!\n\n"
        f"Choose an option below:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

async def settings_terms_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔒 Privacy Policy", callback_data="terms_privacy")],
        [InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")]
    ]
    
    terms_text = (
        "📋 *Terms and Conditions*\n\n"
        "📄 *Last Updated:* October 2024\n\n"
        "Welcome to HustleX! By using our bot, you agree to these terms:\n\n"
        "✅ *Usage Rights:*\n"
        "• You may use HustleX for legitimate job searching and posting\n"
        "• All posted jobs must be real and legal opportunities\n\n"
        "🚫 *Prohibited Activities:*\n"
        "• Posting fake or misleading job offers\n"
        "• Spam or harassment of other users\n"
        "• Sharing inappropriate content\n\n"
        "🛡️ *Privacy:*\n"
        "• We protect your personal information\n"
        "• CVs are stored securely and only shared with your consent\n\n"
        "📞 *Contact:* @HustleXSupport for questions"
    )
    
    await safe_edit_message(
        q,
        terms_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

# ---------------------------
# Additional Settings Handlers
# ---------------------------
async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    # Extract language code from callback data
    lang_code = q.data.split('_')[1]
    user_id = update.effective_user.id
    
    # Store the user's language preference
    user_languages[user_id] = lang_code
    
    lang_names = {
        'en': '🇺🇸 English',
        'es': '🇪🇸 Español', 
        'fr': '🇫🇷 Français',
        'de': '🇩🇪 Deutsch',
        'it': '🇮🇹 Italiano',
        'pt': '🇵🇹 Português',
        'am': '🇪🇹 አማርኛ (Amharic)'
    }
    
    selected_lang = lang_names.get(lang_code, 'English')
    
    # Language-specific confirmation messages
    confirmation_messages = {
        'en': {
            'title': "✅ *Language Updated!*",
            'message': f"🌍 *Selected Language:* {selected_lang}\n\n📝 All bot messages will now be displayed in your selected language.",
            'back': "⬅️ Back to Languages"
        },
        'es': {
            'title': "✅ *¡Idioma Actualizado!*",
            'message': f"🌍 *Idioma Seleccionado:* {selected_lang}\n\n📝 Todos los mensajes del bot ahora se mostrarán en tu idioma seleccionado.",
            'back': "⬅️ Volver a Idiomas"
        },
        'fr': {
            'title': "✅ *Langue Mise à Jour!*",
            'message': f"🌍 *Langue Sélectionnée:* {selected_lang}\n\n📝 Tous les messages du bot s'afficheront maintenant dans votre langue sélectionnée.",
            'back': "⬅️ Retour aux Langues"
        },
        'de': {
            'title': "✅ *Sprache Aktualisiert!*",
            'message': f"🌍 *Ausgewählte Sprache:* {selected_lang}\n\n📝 Alle Bot-Nachrichten werden jetzt in Ihrer ausgewählten Sprache angezeigt.",
            'back': "⬅️ Zurück zu Sprachen"
        },
        'it': {
            'title': "✅ *Lingua Aggiornata!*",
            'message': f"🌍 *Lingua Selezionata:* {selected_lang}\n\n📝 Tutti i messaggi del bot ora verranno visualizzati nella tua lingua selezionata.",
            'back': "⬅️ Torna alle Lingue"
        },
        'pt': {
            'title': "✅ *Idioma Atualizado!*",
            'message': f"🌍 *Idioma Selecionado:* {selected_lang}\n\n📝 Todas as mensagens do bot agora serão exibidas no seu idioma selecionado.",
            'back': "⬅️ Voltar aos Idiomas"
        },
        'am': {
            'title': "✅ *ቋንቋ ተዘምኗል!*",
            'message': f"🌍 *የተመረጠ ቋንቋ:* {selected_lang}\n\n📝 ሁሉም የቦት መልዕክቶች አሁን በተመረጠዎ ቋንቋ ይታያሉ።",
            'back': "⬅️ ወደ ቋንቋዎች ይመለሱ"
        }
    }
    
    messages = confirmation_messages.get(lang_code, confirmation_messages['en'])
    
    keyboard = [
        [InlineKeyboardButton(messages['back'], callback_data="settings_languages")]
    ]
    
    await safe_edit_message(
        q,
        f"{messages['title']}\n\n{messages['message']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

async def cv_upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Back to My CV", callback_data="settings_cv")]
    ]
    
    await safe_edit_message(
        q,
        "📤 *Upload CV*\n\n"
        "📎 Please send your CV file as a document.\n\n"
        "📝 *Supported formats:*\n"
        "• PDF (.pdf)\n"
        "• Word Document (.docx)\n\n"
        "📏 *Requirements:*\n"
        "• Maximum file size: 16 MB\n"
        "• File should be clearly readable\n\n"
        "💡 *Tip:* Make sure your CV is up-to-date with your latest experience!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

async def cv_view_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    
    if user_id in user_cvs and user_cvs[user_id] is not None:
        cv_info = user_cvs[user_id]
        keyboard = [
            [InlineKeyboardButton("📤 Upload New CV", callback_data="cv_upload")],
            [InlineKeyboardButton("🗑️ Remove CV", callback_data="cv_remove")],
            [InlineKeyboardButton("⬅️ Back to My CV", callback_data="settings_cv")]
        ]
        
        await safe_edit_message(
            q,
            f"👁️ *View CV*\n\n"
            f"📁 *File:* {cv_info.get('filename', 'Unknown')}\n"
            f"📏 *Size:* {cv_info.get('file_size', 'Unknown')} bytes\n"
            f"📅 *Uploaded:* {cv_info.get('upload_date', 'Unknown')}\n\n"
            f"📝 *Your CV is ready for:*\n"
            f"• Sharing with potential employers\n"
            f"• Job applications through HustleX\n"
            f"• Profile showcasing\n\n"
            f"💼 *Want to update or remove your CV?*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            context=context
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📤 Upload New CV", callback_data="cv_upload")],
            [InlineKeyboardButton("⬅️ Back to My CV", callback_data="settings_cv")]
        ]
        
        await safe_edit_message(
            q,
            "👁️ *View CV*\n\n"
            "📁 *Status:* No CV uploaded yet\n\n"
            "📝 Once you upload a CV, you'll be able to:\n"
            "• Preview your CV\n"
            "• Download a copy\n"
            "• Share it with potential employers\n"
            "• Update it anytime\n\n"
            "💼 *Ready to upload your CV?*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            context=context
        )

# ---------------------------
# CV Removal Handler
# ---------------------------
async def cv_remove_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    
    # Check if user has a CV
    if user_id in user_cvs and user_cvs[user_id] is not None:
        # Remove the CV from storage
        del user_cvs[user_id]
        
        keyboard = [
            [InlineKeyboardButton("📤 Upload New CV", callback_data="cv_upload")],
            [InlineKeyboardButton("⬅️ Back to My CV", callback_data="settings_cv")]
        ]
        
        await safe_edit_message(
            q,
            "🗑️ *CV Removed Successfully*\n\n"
            "✅ Your CV has been permanently deleted from our system.\n\n"
            "📝 *What's next?*\n"
            "• Upload a new CV anytime\n"
            "• Your profile remains active\n"
            "• Previous job applications are unaffected\n\n"
            "💼 *Ready to upload a new CV?*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            context=context
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📤 Upload CV", callback_data="cv_upload")],
            [InlineKeyboardButton("⬅️ Back to My CV", callback_data="settings_cv")]
        ]
        
        await safe_edit_message(
            q,
            "❌ *No CV Found*\n\n"
            "There's no CV to remove. You haven't uploaded one yet.\n\n"
            "💼 *Want to upload your CV?*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            context=context
        )

# ---------------------------
# Account Management Handlers
# ---------------------------
async def account_edit_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Inherit profile from Telegram only
    name = f"{user.first_name or 'Not set'} {user.last_name or ''}".strip()
    telegram_username = f"@{user.username}" if user.username else "Not set"
    has_photo = False
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Account", callback_data="settings_account")]
    ]
    
    await safe_edit_message(
        q,
        f"👤 *Profile*\n\n"
        f"• Name: {name}\n"
        f"• Username: {telegram_username}\n"
        f"• User ID: {user.id}\n\n"
        f"ℹ️ Profile data is inherited from Telegram and not editable here.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

# Name editing handler
async def edit_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    # Get user's language preference
    user_id = update.effective_user.id
    lang_code = user_languages.get(user_id, 'en')
    
    # Language-specific messages
    title = {
        'en': "📝 *Edit Name*",
        'es': "📝 *Editar Nombre*",
        'fr': "📝 *Modifier le Nom*",
        'de': "📝 *Name Bearbeiten*",
        'it': "📝 *Modifica Nome*",
        'pt': "📝 *Editar Nome*",
        'am': "📝 *ስም ማስተካከል*"
    }.get(lang_code, "📝 *Edit Name*")
    
    prompt = {
        'en': "Please send your new name as a message.",
        'es': "Por favor, envía tu nuevo nombre como mensaje.",
        'fr': "Veuillez envoyer votre nouveau nom en message.",
        'de': "Bitte senden Sie Ihren neuen Namen als Nachricht.",
        'it': "Invia il tuo nuovo nome come messaggio.",
        'pt': "Por favor, envie seu novo nome como mensagem.",
        'am': "እባክዎ አዲስ ስምዎን እንደ መልዕክት ይላኩ።"
    }.get(lang_code, "Please send your new name as a message.")
    
    note = {
        'en': "💡 *Note:* This will be used for your HustleX profile and job applications.",
        'es': "💡 *Nota:* Esto se utilizará para tu perfil de HustleX y solicitudes de trabajo.",
        'fr': "💡 *Remarque:* Ceci sera utilisé pour votre profil HustleX et vos candidatures.",
        'de': "💡 *Hinweis:* Dies wird für Ihr HustleX-Profil und Bewerbungen verwendet.",
        'it': "💡 *Nota:* Questo sarà utilizzato per il tuo profilo HustleX e le candidature di lavoro.",
        'pt': "💡 *Nota:* Isso será usado para seu perfil HustleX e candidaturas a empregos.",
        'am': "💡 *ማሳሰቢያ:* ይህ ለ HustleX መገለጫዎ እና ለሥራ ማመልከቻዎች ጥቅም ላይ ይውላል።"
    }.get(lang_code, "💡 *Note:* This will be used for your HustleX profile and job applications.")
    
    back_text = {
        'en': "⬅️ Back to Profile",
        'es': "⬅️ Volver al Perfil",
        'fr': "⬅️ Retour au Profil",
        'de': "⬅️ Zurück zum Profil",
        'it': "⬅️ Torna al Profilo",
        'pt': "⬅️ Voltar ao Perfil",
        'am': "⬅️ ወደ መገለጫ ይመለሱ"
    }.get(lang_code, "⬅️ Back to Profile")
    
    keyboard = [
        [InlineKeyboardButton(back_text, callback_data="account_edit_profile")]
    ]
    
    await safe_edit_message(
        q,
        f"{title}\n\n"
        f"{prompt}\n\n"
        f"{note}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )
    
    # Store that we're waiting for a name input
    context.user_data['awaiting_input'] = 'name'

# Contact info editing handler
async def edit_contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    # Get user's language preference
    user_id = update.effective_user.id
    lang_code = user_languages.get(user_id, 'en')
    
    # Language-specific messages
    title = {
        'en': "📞 *Edit Contact Information*",
        'es': "📞 *Editar Información de Contacto*",
        'fr': "📞 *Modifier les Coordonnées*",
        'de': "📞 *Kontaktinformationen Bearbeiten*",
        'it': "📞 *Modifica Informazioni di Contatto*",
        'pt': "📞 *Editar Informações de Contato*",
        'am': "📞 *የመገኛ መረጃ ማስተካከል*"
    }.get(lang_code, "📞 *Edit Contact Information*")
    
    prompt = {
        'en': "Please send your contact information as a message.",
        'es': "Por favor, envía tu información de contacto como mensaje.",
        'fr': "Veuillez envoyer vos coordonnées en message.",
        'de': "Bitte senden Sie Ihre Kontaktinformationen als Nachricht.",
        'it': "Invia le tue informazioni di contatto come messaggio.",
        'pt': "Por favor, envie suas informações de contato como mensagem.",
        'am': "እባክዎ የመገኛ መረጃዎን እንደ መልዕክት ይላኩ።"
    }.get(lang_code, "Please send your contact information as a message.")
    
    tip = {
        'en': "💡 *Tip:* You can include email, phone number, or other preferred contact methods.",
        'es': "💡 *Consejo:* Puedes incluir correo electrónico, número de teléfono u otros métodos de contacto preferidos.",
        'fr': "💡 *Conseil:* Vous pouvez inclure email, numéro de téléphone ou autres méthodes de contact préférées.",
        'de': "💡 *Tipp:* Sie können E-Mail, Telefonnummer oder andere bevorzugte Kontaktmethoden angeben.",
        'it': "💡 *Suggerimento:* Puoi includere email, numero di telefono o altri metodi di contatto preferiti.",
        'pt': "💡 *Dica:* Você pode incluir email, número de telefone ou outros métodos de contato preferidos.",
        'am': "💡 *ምክር:* ኢሜይል፣ ስልክ ቁጥር ወይም ሌሎች የሚመርጧቸውን የመገናኛ ዘዴዎች ማካተት ይችላሉ።"
    }.get(lang_code, "💡 *Tip:* You can include email, phone number, or other preferred contact methods.")
    
    back_text = {
        'en': "⬅️ Back to Profile",
        'es': "⬅️ Volver al Perfil",
        'fr': "⬅️ Retour au Profil",
        'de': "⬅️ Zurück zum Profil",
        'it': "⬅️ Torna al Profilo",
        'pt': "⬅️ Voltar ao Perfil",
        'am': "⬅️ ወደ መገለጫ ይመለሱ"
    }.get(lang_code, "⬅️ Back to Profile")
    
    keyboard = [
        [InlineKeyboardButton(back_text, callback_data="account_edit_profile")]
    ]
    
    await safe_edit_message(
        q,
        f"{title}\n\n"
        f"{prompt}\n\n"
        f"{tip}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )
    
    # Store that we're waiting for contact info input
    context.user_data['awaiting_input'] = 'contact'

# Age editing handler
async def edit_age_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    # Get user's language preference
    user_id = update.effective_user.id
    lang_code = user_languages.get(user_id, 'en')
    
    # Language-specific messages
    title = {
        'en': "🎂 *Edit Age*",
        'es': "🎂 *Editar Edad*",
        'fr': "🎂 *Modifier l'Âge*",
        'de': "🎂 *Alter Bearbeiten*",
        'it': "🎂 *Modifica Età*",
        'pt': "🎂 *Editar Idade*",
        'am': "🎂 *እድሜ ማስተካከል*"
    }.get(lang_code, "🎂 *Edit Age*")
    
    prompt = {
        'en': "Please send your age as a number.",
        'es': "Por favor, envía tu edad como un número.",
        'fr': "Veuillez envoyer votre âge sous forme de nombre.",
        'de': "Bitte senden Sie Ihr Alter als Zahl.",
        'it': "Invia la tua età come numero.",
        'pt': "Por favor, envie sua idade como um número.",
        'am': "እባክዎ እድሜዎን እንደ ቁጥር ይላኩ።"
    }.get(lang_code, "Please send your age as a number.")
    
    note = {
        'en': "💡 *Note:* This information will be used for job matching and statistics.",
        'es': "💡 *Nota:* Esta información se utilizará para la coincidencia de trabajos y estadísticas.",
        'fr': "💡 *Remarque:* Ces informations seront utilisées pour la correspondance d'emploi et les statistiques.",
        'de': "💡 *Hinweis:* Diese Information wird für Job-Matching und Statistiken verwendet.",
        'it': "💡 *Nota:* Queste informazioni saranno utilizzate per l'abbinamento di lavoro e le statistiche.",
        'pt': "💡 *Nota:* Esta informação será usada para correspondência de emprego e estatísticas.",
        'am': "💡 *ማሳሰቢያ:* ይህ መረጃ ለሥራ ማዛመድ እና ለስታቲስቲክስ ጥቅም ላይ ይውላል።"
    }.get(lang_code, "💡 *Note:* This information will be used for job matching and statistics.")
    
    back_text = {
        'en': "⬅️ Back to Profile",
        'es': "⬅️ Volver al Perfil",
        'fr': "⬅️ Retour au Profil",
        'de': "⬅️ Zurück zum Profil",
        'it': "⬅️ Torna al Profilo",
        'pt': "⬅️ Voltar ao Perfil",
        'am': "⬅️ ወደ መገለጫ ይመለሱ"
    }.get(lang_code, "⬅️ Back to Profile")
    
    keyboard = [
        [InlineKeyboardButton(back_text, callback_data="account_edit_profile")]
    ]
    
    await safe_edit_message(
        q,
        f"{title}\n\n"
        f"{prompt}\n\n"
        f"{note}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )
    
    # Store that we're waiting for age input
    context.user_data['awaiting_input'] = 'age'

# Profile photo update handler
async def edit_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    # Get user's language preference
    user_id = update.effective_user.id
    lang_code = user_languages.get(user_id, 'en')
    
    # Language-specific messages
    title = {
        'en': "📸 *Update Profile Photo*",
        'es': "📸 *Actualizar Foto de Perfil*",
        'fr': "📸 *Mettre à Jour la Photo de Profil*",
        'de': "📸 *Profilbild Aktualisieren*",
        'it': "📸 *Aggiorna Foto Profilo*",
        'pt': "📸 *Atualizar Foto de Perfil*",
        'am': "📸 *የመገለጫ ፎቶ ማዘመን*"
    }.get(lang_code, "📸 *Update Profile Photo*")
    
    prompt = {
        'en': "Please send a new photo for your profile.",
        'es': "Por favor, envía una nueva foto para tu perfil.",
        'fr': "Veuillez envoyer une nouvelle photo pour votre profil.",
        'de': "Bitte senden Sie ein neues Foto für Ihr Profil.",
        'it': "Invia una nuova foto per il tuo profilo.",
        'pt': "Por favor, envie uma nova foto para o seu perfil.",
        'am': "እባክዎ ለመገለጫዎ አዲስ ፎቶ ይላኩ።"
    }.get(lang_code, "Please send a new photo for your profile.")
    
    tip = {
        'en': "💡 *Tip:* A professional profile photo increases your chances of getting hired!",
        'es': "💡 *Consejo:* ¡Una foto de perfil profesional aumenta tus posibilidades de ser contratado!",
        'fr': "💡 *Conseil:* Une photo de profil professionnelle augmente vos chances d'être embauché !",
        'de': "💡 *Tipp:* Ein professionelles Profilbild erhöht Ihre Chancen, eingestellt zu werden!",
        'it': "💡 *Suggerimento:* Una foto profilo professionale aumenta le tue possibilità di essere assunto!",
        'pt': "💡 *Dica:* Uma foto de perfil profissional aumenta suas chances de ser contratado!",
        'am': "💡 *ምክር:* ሙያዊ የመገለጫ ፎቶ የመቀጠር እድልዎን ይጨምራል!"
    }.get(lang_code, "💡 *Tip:* A professional profile photo increases your chances of getting hired!")
    
    back_text = {
        'en': "⬅️ Back to Profile",
        'es': "⬅️ Volver al Perfil",
        'fr': "⬅️ Retour au Profil",
        'de': "⬅️ Zurück zum Profil",
        'it': "⬅️ Torna al Profilo",
        'pt': "⬅️ Voltar ao Perfil",
        'am': "⬅️ ወደ መገለጫ ይመለሱ"
    }.get(lang_code, "⬅️ Back to Profile")
    
    keyboard = [
        [InlineKeyboardButton(back_text, callback_data="account_edit_profile")]
    ]
    
    await safe_edit_message(
        q,
        f"{title}\n\n"
        f"{prompt}\n\n"
        f"{tip}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )
    
    # Store that we're waiting for a photo input
    context.user_data['awaiting_input'] = 'photo'

# Handler for text messages when awaiting specific input
async def text_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Get user's language preference
    lang_code = user_languages.get(user_id, 'en')
    
    # Initialize user profile if not exists
    if user_id not in user_profiles:
        user_profiles[user_id] = {}
    
    # Language-specific back button text
    back_text = {
        'en': "⬅️ Back to Profile",
        'es': "⬅️ Volver al Perfil",
        'fr': "⬅️ Retour au Profil",
        'de': "⬅️ Zurück zum Profil",
        'it': "⬅️ Torna al Profilo",
        'pt': "⬅️ Voltar ao Perfil",
        'am': "⬅️ ወደ መገለጫ ይመለሱ"
    }.get(lang_code, "⬅️ Back to Profile")
    
    keyboard = [
        [InlineKeyboardButton(back_text, callback_data="account_edit_profile")]
    ]
    
    # Check what kind of input we're waiting for
    if context.user_data.get('awaiting_input') == 'name':
        # Store the new name
        user_profiles[user_id]['custom_name'] = message_text
        
        # Clear the awaiting input flag
        context.user_data.pop('awaiting_input', None)
        
        # Language-specific messages
        title = {
            'en': "✅ *Name Updated Successfully!*",
            'es': "✅ *¡Nombre Actualizado Exitosamente!*",
            'fr': "✅ *Nom Mis à Jour avec Succès!*",
            'de': "✅ *Name Erfolgreich Aktualisiert!*",
            'it': "✅ *Nome Aggiornato con Successo!*",
            'pt': "✅ *Nome Atualizado com Sucesso!*",
            'am': "✅ *ስም በተሳካ ሁኔታ ተዘምኗል!*"
        }.get(lang_code, "✅ *Name Updated Successfully!*")
        
        updated_to = {
            'en': f"Your profile name has been changed to: *{message_text}*",
            'es': f"Tu nombre de perfil ha sido cambiado a: *{message_text}*",
            'fr': f"Votre nom de profil a été changé à: *{message_text}*",
            'de': f"Ihr Profilname wurde geändert zu: *{message_text}*",
            'it': f"Il tuo nome del profilo è stato cambiato a: *{message_text}*",
            'pt': f"Seu nome de perfil foi alterado para: *{message_text}*",
            'am': f"የመገለጫ ስምዎ ወደ: *{message_text}* ተቀይሯል"
        }.get(lang_code, f"Your profile name has been changed to: *{message_text}*")
        
        note = {
            'en': "This name will be used for all your HustleX activities.",
            'es': "Este nombre se utilizará para todas tus actividades en HustleX.",
            'fr': "Ce nom sera utilisé pour toutes vos activités HustleX.",
            'de': "Dieser Name wird für alle Ihre HustleX-Aktivitäten verwendet.",
            'it': "Questo nome sarà utilizzato per tutte le tue attività su HustleX.",
            'pt': "Este nome será usado para todas as suas atividades no HustleX.",
            'am': "ይህ ስም ለሁሉም የHustleX እንቅስቃሴዎችዎ ጥቅም ላይ ይውላል።"
        }.get(lang_code, "This name will be used for all your HustleX activities.")
        
        # Save profile to API
        await save_profile_to_api(user_id, user_profiles[user_id])
        
        await update.message.reply_text(
            f"{title}\n\n"
            f"{updated_to}\n\n"
            f"{note}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif context.user_data.get('awaiting_input') == 'contact':
        # Store the new contact info
        text_input_handler.user_profiles[user_id]['contact_info'] = message_text
        
        # Clear the awaiting input flag
        context.user_data.pop('awaiting_input', None)
        
        # Language-specific messages
        title = {
            'en': "✅ *Contact Information Updated Successfully!*",
            'es': "✅ *¡Información de Contacto Actualizada Exitosamente!*",
            'fr': "✅ *Coordonnées Mises à Jour avec Succès!*",
            'de': "✅ *Kontaktinformationen Erfolgreich Aktualisiert!*",
            'it': "✅ *Informazioni di Contatto Aggiornate con Successo!*",
            'pt': "✅ *Informações de Contato Atualizadas com Sucesso!*",
            'am': "✅ *የመገኛ መረጃ በተሳካ ሁኔታ ተዘምኗል!*"
        }.get(lang_code, "✅ *Contact Information Updated Successfully!*")
        
        updated_to = {
            'en': f"Your contact information has been updated to: *{message_text}*",
            'es': f"Tu información de contacto ha sido actualizada a: *{message_text}*",
            'fr': f"Vos coordonnées ont été mises à jour à: *{message_text}*",
            'de': f"Ihre Kontaktinformationen wurden aktualisiert auf: *{message_text}*",
            'it': f"Le tue informazioni di contatto sono state aggiornate a: *{message_text}*",
            'pt': f"Suas informações de contato foram atualizadas para: *{message_text}*",
            'am': f"የመገኛ መረጃዎ ወደ: *{message_text}* ተዘምኗል"
        }.get(lang_code, f"Your contact information has been updated to: *{message_text}*")
        
        note = {
            'en': "This will be used for employers to reach you.",
            'es': "Esto será utilizado por los empleadores para contactarte.",
            'fr': "Cela sera utilisé par les employeurs pour vous contacter.",
            'de': "Dies wird von Arbeitgebern verwendet, um Sie zu kontaktieren.",
            'it': "Questo sarà utilizzato dai datori di lavoro per contattarti.",
            'pt': "Isso será usado pelos empregadores para entrar em contato com você.",
            'am': "ይህ አሰሪዎች እርስዎን ለማግኘት ጥቅም ላይ ይውላል።"
        }.get(lang_code, "This will be used for employers to reach you.")
        
        # Save profile to API
        await save_profile_to_api(user_id, user_profiles[user_id])
        
        await update.message.reply_text(
            f"{title}\n\n"
            f"{updated_to}\n\n"
            f"{note}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif context.user_data.get('awaiting_input') == 'age':
        # Validate age input
        try:
            age = int(message_text)
            if age < 16 or age > 100:
                # Invalid age error messages
                error_title = {
                    'en': "❌ *Invalid Age*",
                    'es': "❌ *Edad Inválida*",
                    'fr': "❌ *Âge Invalide*",
                    'de': "❌ *Ungültiges Alter*",
                    'it': "❌ *Età Non Valida*",
                    'pt': "❌ *Idade Inválida*",
                    'am': "❌ *ልክ ያልሆነ እድሜ*"
                }.get(lang_code, "❌ *Invalid Age*")
                
                error_msg = {
                    'en': "Please enter a valid age between 16 and 100.",
                    'es': "Por favor, introduce una edad válida entre 16 y 100.",
                    'fr': "Veuillez entrer un âge valide entre 16 et 100.",
                    'de': "Bitte geben Sie ein gültiges Alter zwischen 16 und 100 ein.",
                    'it': "Inserisci un'età valida tra 16 e 100.",
                    'pt': "Por favor, insira uma idade válida entre 16 e 100.",
                    'am': "እባክዎ ከ16 እና 100 መካከል ያለ ትክክለኛ እድሜ ያስገቡ።"
                }.get(lang_code, "Please enter a valid age between 16 and 100.")
                
                await update.message.reply_text(
                    f"{error_title}\n\n"
                    f"{error_msg}",
                    parse_mode="Markdown"
                )
                return
                
            # Store the new age
            user_profiles[user_id]['age'] = age
            
            # Clear the awaiting input flag
            context.user_data.pop('awaiting_input', None)
            
            # Language-specific messages
            title = {
                'en': "✅ *Age Updated Successfully!*",
                'es': "✅ *¡Edad Actualizada Exitosamente!*",
                'fr': "✅ *Âge Mis à Jour avec Succès!*",
                'de': "✅ *Alter Erfolgreich Aktualisiert!*",
                'it': "✅ *Età Aggiornata con Successo!*",
                'pt': "✅ *Idade Atualizada com Sucesso!*",
                'am': "✅ *እድሜ በተሳካ ሁኔታ ተዘምኗል!*"
            }.get(lang_code, "✅ *Age Updated Successfully!*")
            
            updated_to = {
                'en': f"Your age has been updated to: *{age}*",
                'es': f"Tu edad ha sido actualizada a: *{age}*",
                'fr': f"Votre âge a été mis à jour à: *{age}*",
                'de': f"Ihr Alter wurde aktualisiert auf: *{age}*",
                'it': f"La tua età è stata aggiornata a: *{age}*",
                'pt': f"Sua idade foi atualizada para: *{age}*",
                'am': f"እድሜዎ ወደ: *{age}* ተዘምኗል"
            }.get(lang_code, f"Your age has been updated to: *{age}*")
            
            note = {
                'en': "This information will be used for job matching.",
                'es': "Esta información se utilizará para la coincidencia de trabajos.",
                'fr': "Cette information sera utilisée pour la correspondance d'emploi.",
                'de': "Diese Information wird für Job-Matching verwendet.",
                'it': "Questa informazione sarà utilizzata per l'abbinamento di lavoro.",
                'pt': "Esta informação será usada para correspondência de emprego.",
                'am': "ይህ መረጃ ለሥራ ማዛመድ ጥቅም ላይ ይውላል።"
            }.get(lang_code, "This information will be used for job matching.")
            
            # Save profile to API
            await save_profile_to_api(user_id, user_profiles[user_id])
            
            await update.message.reply_text(
                f"{title}\n\n"
                f"{updated_to}\n\n"
                f"{note}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except ValueError:
            # Invalid input error messages
            error_title = {
                'en': "❌ *Invalid Input*",
                'es': "❌ *Entrada Inválida*",
                'fr': "❌ *Entrée Invalide*",
                'de': "❌ *Ungültige Eingabe*",
                'it': "❌ *Input Non Valido*",
                'pt': "❌ *Entrada Inválida*",
                'am': "❌ *ልክ ያልሆነ ግብዓት*"
            }.get(lang_code, "❌ *Invalid Input*")
            
            error_msg = {
                'en': "Please enter your age as a number.",
                'es': "Por favor, introduce tu edad como un número.",
                'fr': "Veuillez entrer votre âge sous forme de nombre.",
                'de': "Bitte geben Sie Ihr Alter als Zahl ein.",
                'it': "Inserisci la tua età come numero.",
                'pt': "Por favor, insira sua idade como um número.",
                'am': "እባክዎ እድሜዎን እንደ ቁጥር ያስገቡ።"
            }.get(lang_code, "Please enter your age as a number.")
            
            await update.message.reply_text(
                f"{error_title}\n\n"
                f"{error_msg}",
                parse_mode="Markdown"
            )


async def account_notifications_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    # Simple notification preferences storage (in production, use database)
    if not hasattr(account_notifications_handler, 'user_notifications'):
        account_notifications_handler.user_notifications = {}
    
    user_prefs = account_notifications_handler.user_notifications.get(user_id, {
        'job_alerts': True,
        'application_updates': True,
        'messages': True,
        'marketing': False
    })
    
    keyboard = [
        [InlineKeyboardButton(f"🚨 Job Alerts: {'✅ ON' if user_prefs['job_alerts'] else '❌ OFF'}", 
                             callback_data="toggle_job_alerts")],
        [InlineKeyboardButton(f"📄 Application Updates: {'✅ ON' if user_prefs['application_updates'] else '❌ OFF'}", 
                             callback_data="toggle_app_updates")],
        [InlineKeyboardButton(f"💬 Messages: {'✅ ON' if user_prefs['messages'] else '❌ OFF'}", 
                             callback_data="toggle_messages")],
        [InlineKeyboardButton(f"📢 Marketing: {'✅ ON' if user_prefs['marketing'] else '❌ OFF'}", 
                             callback_data="toggle_marketing")],
        [InlineKeyboardButton("⬅️ Back to Account", callback_data="settings_account")]
    ]
    
    await safe_edit_message(
        q,
        f"🔔 *Notification Settings*\n\n"
        f"📱 *Manage your notification preferences:*\n\n"
        f"🚨 *Job Alerts:* Get notified about new jobs\n"
        f"📄 *Application Updates:* Status changes on your applications\n"
        f"💬 *Messages:* Direct messages from employers\n"
        f"📢 *Marketing:* Updates about HustleX features\n\n"
        f"💡 *Tip:* You can toggle each notification type on/off below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

async def account_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚠️ Yes, Delete My Account", callback_data="confirm_delete_account")],
        [InlineKeyboardButton("❌ Cancel", callback_data="settings_account")]
    ]
    
    await safe_edit_message(
        q,
        f"🗑️ *Delete Account*\n\n"
        f"⚠️ *WARNING:* This action is permanent and cannot be undone!\n\n"
        f"🔥 *What will be deleted:*\n"
        f"• Your profile information\n"
        f"• Uploaded CV and documents\n"
        f"• Job application history\n"
        f"• All saved preferences\n\n"
        f"📞 *Alternative:* You can temporarily disable notifications instead.\n\n"
        f"❓ *Are you sure you want to permanently delete your account?*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

async def privacy_policy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Back to Terms", callback_data="settings_terms")]
    ]
    
    privacy_text = (
        "🔒 *Privacy Policy*\n\n"
        "📄 *Last Updated:* October 2024\n\n"
        "Your privacy is important to us. Here's how we protect your data:\n\n"
        "📊 *Data We Collect:*\n"
        "• Basic profile information (name, username)\n"
        "• CVs and documents you upload\n"
        "• Job application history\n"
        "• Usage analytics (anonymous)\n\n"
        "🛡️ *How We Protect Your Data:*\n"
        "• Encrypted storage of all personal information\n"
        "• Secure file handling for CVs and documents\n"
        "• No sharing of personal data with third parties\n"
        "• Regular security audits and updates\n\n"
        "🎯 *How We Use Your Data:*\n"
        "• Matching you with relevant job opportunities\n"
        "• Improving our service quality\n"
        "• Sending important notifications (if enabled)\n\n"
        "🗑️ *Your Rights:*\n"
        "• Request data deletion at any time\n"
        "• Access your stored information\n"
        "• Opt-out of data processing\n\n"
        "📞 *Contact:* @HustleXSupport for privacy questions"
    )
    
    await safe_edit_message(
        q,
        privacy_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

# ---------------------------
# Notification Toggle Handlers
# ---------------------------
async def toggle_notification_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    toggle_type = q.data.split('_', 1)[1]  # get part after 'toggle_'
    
    # Initialize user notifications if not exists
    if not hasattr(account_notifications_handler, 'user_notifications'):
        account_notifications_handler.user_notifications = {}
    
    if user_id not in account_notifications_handler.user_notifications:
        account_notifications_handler.user_notifications[user_id] = {
            'job_alerts': True,
            'application_updates': True,
            'messages': True,
            'marketing': False
        }
    
    # Toggle the specific notification type
    current_prefs = account_notifications_handler.user_notifications[user_id]
    if toggle_type == 'job_alerts':
        current_prefs['job_alerts'] = not current_prefs['job_alerts']
        setting_name = "Job Alerts"
    elif toggle_type == 'app_updates':
        current_prefs['application_updates'] = not current_prefs['application_updates']
        setting_name = "Application Updates"
    elif toggle_type == 'messages':
        current_prefs['messages'] = not current_prefs['messages']
        setting_name = "Messages"
    elif toggle_type == 'marketing':
        current_prefs['marketing'] = not current_prefs['marketing']
        setting_name = "Marketing"
    
    # Show updated notification settings
    await account_notifications_handler(update, context)

async def confirm_delete_account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    user_id = update.effective_user.id
    
    # Remove user data
    if user_id in user_cvs:
        del user_cvs[user_id]
    
    if hasattr(account_notifications_handler, 'user_notifications'):
        if user_id in account_notifications_handler.user_notifications:
            del account_notifications_handler.user_notifications[user_id]
    
    keyboard = [
        [InlineKeyboardButton("🏠 Start Over", callback_data="menu")]
    ]
    
    await safe_edit_message(
        q,
        f"✅ *Account Deleted Successfully*\n\n"
        f"🗑️ Your account has been permanently deleted from HustleX.\n\n"
        f"📋 *What was removed:*\n"
        f"• Profile information\n"
        f"• Uploaded CV and documents\n"
        f"• Notification preferences\n"
        f"• All saved data\n\n"
        f"👋 Thank you for using HustleX. You can create a new account anytime by using /start.\n\n"
        f"💬 If you have feedback, contact @HustleXSupport",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
        context=context
    )

# ---------------------------
# Profile API Integration
# ---------------------------
async def save_profile_to_api(user_id, profile_data):
    """Save user profile data to the API"""
    try:
        # Prepare the data for API request
        form_data = {
            "name": profile_data.get('custom_name', ''),
            "age": profile_data.get('age', 0),
            "sex": profile_data.get('sex', 'Not specified'),
            "contact_info": profile_data.get('contact_info', ''),
            "init_data": f"user_id={user_id}"  # Simple init_data for demo purposes
        }
        
        # If we have a profile picture, we would need to download it and send as a file
        profile_pic_file_id = profile_data.get('profile_pic_file_id')
        
        # In a real implementation, you would:
        # 1. Download the file using context.bot.get_file(file_id)
        # 2. Send the file as part of a multipart/form-data request
        # 3. Handle the API response
        
        # For now, we'll just log that we would send this data
        logger.info(f"Would send profile data to API for user {user_id}: {form_data}")
        
        # In production, you would make an actual API call here
        # Example with aiohttp:
        # async with aiohttp.ClientSession() as session:
        #     async with session.post('http://api-url/api/profile', data=form_data) as response:
        #         return await response.json()
        
        return True
    except Exception as e:
        logger.error(f"Error saving profile to API: {e}")
        return False

# ---------------------------
# File uploads handler (CV / profile picture)
# ---------------------------
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    user_id = update.effective_user.id
    
    # Check if we're waiting for a profile photo
    awaiting_photo = context.user_data.get('awaiting_input') == 'photo'
    
    if m.document:
        # Check if it's a CV file (PDF or DOCX)
        file_name = m.document.file_name or "document"
        file_size = m.document.file_size
        mime_type = m.document.mime_type
        
        # Validate file type
        if file_name.lower().endswith(('.pdf', '.docx')) or mime_type in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            # Store CV information
            user_cvs[user_id] = {
                'file_id': m.document.file_id,
                'filename': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
                'upload_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            keyboard = [
                [InlineKeyboardButton("👁️ View CV", callback_data="cv_view")],
                [InlineKeyboardButton("📄 My CV Settings", callback_data="settings_cv")]
            ]
            
            await m.reply_text(
                f"✅ *CV Upload Successful!*\n\n"
                f"📁 *File:* {file_name}\n"
                f"📏 *Size:* {file_size:,} bytes\n"
                f"📝 *Type:* {'PDF' if file_name.lower().endswith('.pdf') else 'Word Document'}\n\n"
                f"🎉 Your CV is now ready for job applications!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await m.reply_text(
                "❌ *Invalid File Type*\n\n"
                "Please upload a PDF (.pdf) or Word document (.docx) file.\n\n"
                "📝 *Supported formats:*\n"
                "• PDF (.pdf)\n"
                "• Word Document (.docx)"
            )
            
    elif m.photo:
        file_id = m.photo[-1].file_id
        
        # Initialize user profile if not exists
        if user_id not in user_profiles:
            user_profiles[user_id] = {}
        
        # Store the profile picture file_id
        user_profiles[user_id]['profile_pic_file_id'] = file_id
        
        # Clear the awaiting input flag if we were waiting for a photo
        if awaiting_photo:
            context.user_data.pop('awaiting_input', None)
            
            # Get user's language preference
            lang_code = user_languages.get(user_id, 'en')
            
            # Language-specific messages
            title = {
                'en': "✅ *Profile Photo Updated Successfully!*",
                'es': "✅ *¡Foto de Perfil Actualizada Exitosamente!*",
                'fr': "✅ *Photo de Profil Mise à Jour avec Succès!*",
                'de': "✅ *Profilbild Erfolgreich Aktualisiert!*",
                'it': "✅ *Foto Profilo Aggiornata con Successo!*",
                'pt': "✅ *Foto de Perfil Atualizada com Sucesso!*",
                'am': "✅ *የመገለጫ ፎቶ በተሳካ ሁኔታ ተዘምኗል!*"
            }.get(lang_code, "✅ *Profile Photo Updated Successfully!*")
            
            message = {
                'en': "Your new profile photo has been saved.",
                'es': "Tu nueva foto de perfil ha sido guardada.",
                'fr': "Votre nouvelle photo de profil a été enregistrée.",
                'de': "Ihr neues Profilbild wurde gespeichert.",
                'it': "La tua nuova foto profilo è stata salvata.",
                'pt': "Sua nova foto de perfil foi salva.",
                'am': "አዲሱ የመገለጫ ፎቶዎ ተቀምጧል።"
            }.get(lang_code, "Your new profile photo has been saved.")
            
            tip = {
                'en': "💡 *Tip:* A professional profile photo increases your chances of getting hired!",
                'es': "💡 *Consejo:* ¡Una foto de perfil profesional aumenta tus posibilidades de ser contratado!",
                'fr': "💡 *Conseil:* Une photo de profil professionnelle augmente vos chances d'être embauché !",
                'de': "💡 *Tipp:* Ein professionelles Profilbild erhöht Ihre Chancen, eingestellt zu werden!",
                'it': "💡 *Suggerimento:* Una foto profilo professionale aumenta le tue possibilità di essere assunto!",
                'pt': "💡 *Dica:* Uma foto de perfil profissional aumenta suas chances de ser contratado!",
                'am': "💡 *ምክር:* ሙያዊ የመገለጫ ፎቶ የመቀጠር እድልዎን ይጨምራል!"
            }.get(lang_code, "💡 *Tip:* A professional profile photo increases your chances of getting hired!")
            
            back_text = {
                'en': "⬅️ Back to Profile",
                'es': "⬅️ Volver al Perfil",
                'fr': "⬅️ Retour au Profil",
                'de': "⬅️ Zurück zum Profil",
                'it': "⬅️ Torna al Profilo",
                'pt': "⬅️ Voltar ao Perfil",
                'am': "⬅️ ወደ መገለጫ ይመለሱ"
            }.get(lang_code, "⬅️ Back to Profile")
            
            keyboard = [
                [InlineKeyboardButton(back_text, callback_data="account_edit_profile")]
            ]
            
            # Save profile to API
            await save_profile_to_api(user_id, user_profiles[user_id])
            
            await m.reply_text(
                f"{title}\n\n"
                f"{message}\n\n"
                f"{tip}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await m.reply_text(
                "📸 Profile picture received — saved.\n\n"
                "💡 *Tip:* You can manage your profile in Settings → Account.",
                parse_mode="Markdown"
            )

# ---------------------------
# Telegram Job Posting Handlers
# ---------------------------
async def post_job_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("📝 Enter Job Title:")
    else:
        await update.message.reply_text("📝 Enter Job Title:")
    return JOB_TITLE

async def job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_title"] = update.message.text
    await update.message.reply_text("Enter Job Type (Full-time, Part-time, Freelance):")
    return JOB_TYPE

async def job_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_type"] = update.message.text
    await update.message.reply_text("Enter Work Location:")
    return WORK_LOCATION

async def work_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["work_location"] = update.message.text
    await update.message.reply_text("Enter Salary:")
    return SALARY

async def salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["salary"] = update.message.text
    await update.message.reply_text("Enter Deadline (YYYY-MM-DD):")
    return DEADLINE

async def deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["deadline"] = update.message.text
    await update.message.reply_text("Enter Job Description:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Enter Client Type (Private / Other):")
    return CLIENT_TYPE

async def client_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["client_type"] = update.message.text
    await update.message.reply_text("Enter Company Name:")
    return COMPANY_NAME

async def company_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["company_name"] = update.message.text
    await update.message.reply_text("Is the company verified? (✅ / No)")
    return VERIFIED

async def verified(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text not in ["yes", "no", "✅"]:
        await update.message.reply_text("Please reply with ✅ or No")
        return VERIFIED
    
    # Set the value to ✅ if the input is 'yes' or the checkmark symbol
    if text == "yes" or text == "✅":
        context.user_data["verified"] = "✅"
    else:
        context.user_data["verified"] = "No"
    await update.message.reply_text("List any previous jobs posted by this company (or type 'None'):")
    return PREVIOUS_JOBS

async def previous_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["previous_jobs"] = update.message.text
    await update.message.reply_text("Enter the link for 'View Details':")
    return JOB_LINK

async def job_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job_link"] = update.message.text
    job_data = context.user_data

    # Validate URL
    def safe_url(url: str) -> str:
        if not url:
            return "https://example.com"
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return "https://example.com"
            return parsed.geturl()
        except Exception as e:
            logger.error(f"Invalid URL {url}: {e}")
            return "https://example.com"

    view_details_url = safe_url(job_data.get("job_link"))
    keyboard = [[InlineKeyboardButton("View Details", url=view_details_url)]]

    # Check channel ID and bot permissions
    CHANNEL_ID = "-1003194542999"  # TODO: Replace with the correct channel ID
    if not await validate_channel_id(context, CHANNEL_ID):
        error_msg = (
            "❌ Error: Invalid channel ID. Please verify the CHANNEL_ID in the bot configuration.\n"
            "To find the correct ID, add the bot to the channel, send a message, and forward it to @userinfobot or @RawDataBot."
        )
        await update.message.reply_text(error_msg)
        logger.error(f"Job posting failed due to invalid CHANNEL_ID: {CHANNEL_ID}")
        return ConversationHandler.END

    if not await check_bot_permissions(context, CHANNEL_ID):
        error_msg = (
            "❌ Error: The bot does not have permission to post in the channel.\n"
            "Please make the bot an admin with 'Send Messages' permission."
        )
        await update.message.reply_text(error_msg)
        logger.error(f"Job posting failed due to insufficient permissions in channel: {CHANNEL_ID}")
        return ConversationHandler.END

    # Build job post with enhanced escaping
    job_text = (
        f"📢 *New Job Posted\\!* \n\n"
        f"*Job Title:* {escape_markdown_v2(job_data['job_title'])}\n"
        f"*Job Type:* {escape_markdown_v2(job_data['job_type'])}\n"
        f"*Location:* {escape_markdown_v2(job_data['work_location'])}\n"
        f"*Salary:* {escape_markdown_v2(job_data['salary'])}\n"
        f"*Deadline:* {escape_markdown_v2(job_data['deadline'])}\n"
        f"*Description:* {escape_markdown_v2(job_data['description'])}\n"
        f"*Client Type:* {escape_markdown_v2(job_data['client_type'])}\n"
        f"*Company Name:* {escape_markdown_v2(job_data['company_name'])}\n"
        f"*Verified:* {escape_markdown_v2('✅') if job_data['verified'].lower() == 'yes' else escape_markdown_v2(job_data['verified'])}\n"
        f"*Previous Jobs:* {escape_markdown_v2(job_data['previous_jobs'])}\n\n"
        f"From: HustleXet\\.com\n"
        f"@HustleXeth\n"
        f"@HustleXet\n"
        f"@HustleXet\\_bot"
    )

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=job_text,
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text("✅ Job posted successfully!")
        logger.info(f"Job posted successfully to channel {CHANNEL_ID}")
        # TODO: Save job_data to database using DATABASE_URL if needed
    except TelegramError as e:
        error_msg = f"❌ Failed to post job: {str(e)}"
        logger.error(f"Failed to post job to channel {CHANNEL_ID}: {e}")
        if "chat not found" in str(e).lower():
            error_msg += "\nThe channel ID is incorrect or the bot is not a member of the channel."
        elif "not found" in str(e).lower():
            error_msg += "\nThe Telegram API returned a 404 error. This could be due to an invalid channel ID or bot token."
        elif "Bad Request: can't parse" in str(e):
            error_msg += "\nInvalid characters in job details. Ensure all fields are properly formatted."
        elif "Too Many Requests" in str(e):
            error_msg += "\nTelegram rate limit exceeded. Please try again later."
        await update.message.reply_text(error_msg)
        return ConversationHandler.END

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Job posting cancelled.")
    return ConversationHandler.END

# ---------------------------
# Main Function
# ---------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and handle them gracefully"""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Handle specific error types
    if "Message to edit not found" in str(context.error):
        # This error is already handled by safe_edit_message, just log it
        logger.info("Message edit failed - message not found")
    elif update and hasattr(update, 'effective_chat') and update.effective_chat:
        # Send a generic error message to the user
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Something went wrong. Please try again or use /start to restart."
            )
        except Exception:
            pass  # If we can't even send a message, just log it

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add error handler
    app.add_error_handler(error_handler)

    # Command handlers
    app.add_handler(CommandHandler("start", start))

    # Job Posting ConversationHandler
    job_post_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(post_job_start, pattern="^post_job_telegram$"),
                      CommandHandler("postjob", post_job_start)],
        states={
            JOB_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_title)],
            JOB_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_type)],
            WORK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_location)],
            SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary)],
            DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deadline)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            CLIENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_type)],
            COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name)],
            VERIFIED: [MessageHandler(filters.TEXT & ~filters.COMMAND, verified)],
            PREVIOUS_JOBS: [MessageHandler(filters.TEXT & ~filters.COMMAND, previous_jobs)],
            JOB_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, job_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True
    )
    app.add_handler(job_post_conv)

    # CallbackQuery handlers
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(applications_cb, pattern="^applications$"))
    app.add_handler(CallbackQueryHandler(about_cb, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(settings_cb, pattern="^settings$"))
    
    # Settings tab handlers
    app.add_handler(CallbackQueryHandler(settings_languages_cb, pattern="^settings_languages$"))
    app.add_handler(CallbackQueryHandler(settings_account_cb, pattern="^settings_account$"))
    app.add_handler(CallbackQueryHandler(settings_cv_cb, pattern="^settings_cv$"))
    app.add_handler(CallbackQueryHandler(settings_terms_cb, pattern="^settings_terms$"))
    
    # Language selection handlers
    app.add_handler(CallbackQueryHandler(language_selection, pattern="^lang_"))
    
    # CV action handlers
    app.add_handler(CallbackQueryHandler(cv_upload_handler, pattern="^cv_upload$"))
    app.add_handler(CallbackQueryHandler(cv_view_handler, pattern="^cv_view$"))
    app.add_handler(CallbackQueryHandler(cv_remove_handler, pattern="^cv_remove$"))
    
    # Account management handlers
    app.add_handler(CallbackQueryHandler(account_edit_profile_handler, pattern="^account_edit_profile$"))
    app.add_handler(CallbackQueryHandler(account_notifications_handler, pattern="^account_notifications$"))
    app.add_handler(CallbackQueryHandler(account_delete_handler, pattern="^account_delete$"))
    app.add_handler(CallbackQueryHandler(privacy_policy_handler, pattern="^terms_privacy$"))
    
    # Notification toggles
    app.add_handler(CallbackQueryHandler(toggle_notification_handler, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(confirm_delete_account_handler, pattern="^confirm_delete_account$"))

    # File/message handlers
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, file_handler))

    # Run bot
    app.run_polling()

if __name__ == "__main__":
    main()
