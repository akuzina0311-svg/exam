import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_service import AIService
from models import Conversation, UserProfile, Program
from app import db, app

logger = logging.getLogger(__name__)

# Get Telegram Bot Token from environment
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "your-bot-token-here").strip()

class ITMOBot:
    def __init__(self):
        self.ai_service = AIService()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not update.effective_user or not update.message:
            return
            
        user = update.effective_user
        welcome_message = """
🎓 Добро пожаловать в бот помощник по магистерским программам ИТМО в области ИИ!

Я помогу вам выбрать между двумя программами:
• **Искусственный интеллект** - техническая программа
• **Управление ИИ-продуктами/AI Product** - продуктовая программа

🔄 **Как это работает:**
1. Сначала я задам вам несколько вопросов о вашем бэкграунде
2. На основе ваших ответов дам персональную рекомендацию
3. Затем отвечу на любые вопросы о программах с учетом вашего профиля

📝 **Начнем с опроса!** Просто напишите любое сообщение, и я начну задавать вопросы о вашем образовании и опыте.
        """
        
        # Create reply keyboard
        keyboard = [
            [KeyboardButton("📝 Начать опрос"), KeyboardButton("❓ Задать вопрос")],
            [KeyboardButton("📊 Сравнить программы"), KeyboardButton("👤 Мой профиль")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        
        # Store user interaction
        with app.app_context():
            self._save_conversation(str(user.id), user.username or "", "/start", welcome_message)

    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        if not update.effective_user or not update.message:
            return
            
        user = update.effective_user
        
        profile_message = """
👤 Расскажите о своем бэкграунде для персональных рекомендаций:

1. Ваш опыт (напишите одно из):
   • technical - технический бэкграунд (программирование, математика, инженерия)
   • product - продуктовый бэкграунд (менеджмент, маркетинг, бизнес)
   • mixed - смешанный опыт
   • beginner - начинающий в области ИИ

2. Количество лет опыта работы (число)

3. Ваши интересы (через запятую):
   • машинное обучение
   • продуктовый менеджмент
   • data science
   • deep learning
   • computer vision
   • nlp
   • стартапы

Пример: technical, 3, машинное обучение, computer vision, стартапы
        """
        
        await update.message.reply_text(profile_message)
        
        with app.app_context():
            self._save_conversation(str(user.id), user.username or "", "/profile", profile_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages"""
        if not update.effective_user or not update.message or not update.message.text:
            return
            
        user = update.effective_user
        message_text = update.message.text
        
        with app.app_context():
            # Check if it's a profile update
            if self._is_profile_update(message_text):
                response = self._update_user_profile(str(user.id), user.username or "", message_text)
                await update.message.reply_text(response)
                self._save_conversation(str(user.id), user.username or "", message_text, response)
                return
            
            # Handle predefined buttons
            if message_text in ["📝 Начать опрос", "Начать опрос"]:
                # Reset user survey to start over
                with app.app_context():
                    user_profile = UserProfile.query.filter_by(telegram_user_id=str(user.id)).first()
                    if user_profile:
                        user_profile.survey_step = 0
                        db.session.commit()
                response = await self.ai_service.generate_response("начать опрос", str(user.id))
            elif message_text in ["📊 Сравнить программы", "Сравнить программы"]:
                response = self._compare_programs()
            elif message_text in ["👤 Мой профиль", "Мой профиль"]:
                response = self._get_user_profile(str(user.id))
            elif message_text in ["❓ Задать вопрос", "Задать вопрос"]:
                response = """
💡 Задайте любой вопрос о программах ИТМО в области ИИ:

• Содержание курсов и дисциплины
• Требования к поступлению  
• Стоимость и сроки обучения
• Карьерные перспективы
• Сравнение программ
• Преподаватели и партнеры

Просто напишите ваш вопрос!
                """
            else:
                # Use AI service for general questions
                response = await self.ai_service.generate_response(message_text, str(user.id))
            
            await update.message.reply_text(response)
            self._save_conversation(str(user.id), user.username or "", message_text, response)

    def _is_profile_update(self, message: str) -> bool:
        """Check if message is a profile update"""
        parts = message.split(',')
        if len(parts) >= 3:
            background_keywords = ['technical', 'product', 'mixed', 'beginner']
            return any(keyword in message.lower() for keyword in background_keywords)
        return False

    def _update_user_profile(self, user_id: str, username: str, message: str) -> str:
        """Update user profile based on message"""
        try:
            parts = [part.strip() for part in message.split(',')]
            if len(parts) < 3:
                return "Неверный формат. Используйте: бэкграунд, годы опыта, интересы"
            
            background = parts[0].lower()
            try:
                experience_years = int(parts[1])
            except ValueError:
                return "Неверный формат годов опыта. Укажите число."
            
            interests = [interest.strip() for interest in parts[2:]]
            
            # Find or create user profile
            profile = UserProfile.query.filter_by(telegram_user_id=str(user_id)).first()
            if profile:
                profile.background = background
                profile.experience_years = experience_years
                profile.interests = interests
                profile.username = username
            else:
                profile = UserProfile()
                profile.telegram_user_id = str(user_id)
                profile.username = username
                profile.background = background
                profile.experience_years = experience_years
                profile.interests = interests
                db.session.add(profile)
            
            db.session.commit()
            
            # Generate personalized recommendation
            recommendation = self._generate_personalized_recommendation(profile)
            
            return f"✅ Профиль обновлен!\n\n{recommendation}"
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return "Ошибка при обновлении профиля. Попробуйте еще раз."

    def _generate_personalized_recommendation(self, profile: UserProfile) -> str:
        """Generate personalized program recommendation"""
        background = profile.background
        interests = profile.interests or []
        experience = profile.experience_years or 0
        
        ai_keywords = ['машинное обучение', 'deep learning', 'computer vision', 'nlp', 'data science']
        product_keywords = ['продуктовый менеджмент', 'стартапы', 'бизнес']
        
        ai_interest_count = sum(1 for interest in interests if any(keyword in interest.lower() for keyword in ai_keywords))
        product_interest_count = sum(1 for interest in interests if any(keyword in interest.lower() for keyword in product_keywords))
        
        recommendation = "🎯 Персональная рекомендация:\n\n"
        
        if background == 'technical' and ai_interest_count > product_interest_count:
            recommendation += """
**Программа "Искусственный интеллект"** больше подходит для вас:

✅ Технический бэкграунд идеально подходит для углубленного изучения ML
✅ Больше технических курсов и проектов
✅ Роли: ML Engineer, Data Engineer, Data Scientist
✅ Научная деятельность и публикации

Рекомендуемые выборные дисциплины:
• Deep Learning и нейронные сети
• Computer Vision
• Natural Language Processing
• MLOps и развертывание моделей
            """
        elif background == 'product' or product_interest_count > ai_interest_count:
            recommendation += """
**Программа "Управление ИИ-продуктами"** больше подходит для вас:

✅ Фокус на продуктовом менеджменте и бизнес-применении ИИ
✅ Проекты с реальными компаниями как Альфа-Банк
✅ Роли: AI Product Manager, AI Project Manager
✅ Изучение вывода ИИ-продуктов на рынок

Рекомендуемые выборные дисциплины:
• Продуктовая аналитика
• AI Product Strategy
• Управление командами разработки
• Монетизация AI-продуктов
            """
        else:
            recommendation += """
**Обе программы могут подойти**, но рассмотрите:

**"Искусственный интеллект"** если хотите:
• Глубже изучить технологии ML/AI
• Заниматься исследованиями
• Работать ML Engineer'ом

**"Управление ИИ-продуктами"** если хотите:
• Управлять AI-продуктами
• Работать на стыке технологий и бизнеса
• Развивать продуктовые навыки
            """
        
        return recommendation

    def _compare_programs(self) -> str:
        """Compare both AI programs"""
        try:
            programs = Program.query.all()
            if len(programs) < 2:
                return "Данные о программах загружаются. Попробуйте позже."
            
            comparison = """
🔄 Сравнение программ ИТМО:

**1. Искусственный интеллект**
• Фокус: Технические аспекты ИИ и ML
• Роли: ML Engineer, Data Engineer, Data Scientist
• Партнеры: X5 Group, Ozon Банк, МТС, Sber AI, Яндекс
• Бюджетных мест: 51-80 (разные направления)
• Особенности: Научная деятельность, публикации

**2. Управление ИИ-продуктами**  
• Фокус: Продуктовый менеджмент ИИ-решений
• Роли: AI Product Manager, AI Project Manager
• Партнеры: Альфа-Банк, АльфаФутуре
• Бюджетных мест: 14
• Особенности: Бизнес-применение ИИ, стартапы

**Общее:**
• Длительность: 2 года
• Стоимость: 599,000 ₽/год
• Язык: русский
• Формат: очное + онлайн
            """
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing programs: {e}")
            return "Ошибка получения данных о программах."

    def _get_user_profile(self, user_id: str) -> str:
        """Get user profile information"""
        try:
            profile = UserProfile.query.filter_by(telegram_user_id=str(user_id)).first()
            if not profile:
                return "Профиль не найден. Используйте /profile для создания."
            
            profile_info = f"""
👤 Ваш профиль:

Бэкграунд: {profile.background}
Опыт: {profile.experience_years} лет
Интересы: {', '.join(profile.interests) if profile.interests else 'не указаны'}

Для обновления профиля используйте /profile
            """
            return profile_info
            
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return "Ошибка получения профиля."

    def _get_career_info(self) -> str:
        """Get career information"""
        return """
💼 Карьерные перспективы:

**Искусственный интеллект:**
• ML Engineer: 170,000 - 300,000+ ₽
• Data Engineer: 150,000 - 280,000 ₽  
• Data Scientist: 180,000 - 350,000 ₽
• Компании: Яндекс, Сбер, МТС, X5 Group

**Управление ИИ-продуктами:**
• AI Product Manager: 150,000 - 400,000+ ₽
• AI Project Manager: 120,000 - 300,000 ₽
• AI Product Analyst: 100,000 - 250,000 ₽
• Компании: Альфа-Банк, стартапы, техкорпорации

Спрос на AI-специалистов растет на 40% в год!
        """

    def _get_admission_info(self) -> str:
        """Get admission information"""
        return """
📝 Как поступить:

**Способы поступления:**
1. Вступительные экзамены (дистанционно)
2. Junior ML Contest (без экзаменов)
3. Конкурс "Портфолио" ИТМО (85+ баллов)
4. МегаОлимпиада ИТМО
5. Олимпиада "Я-профессионал"
6. Рекомендательное письмо

**Ближайшие экзамены:**
• 05.08.2025, 04:00
• 07.08.2025, 04:00  
• 12.08.2025, 04:00

**Документы:** https://abitlk.itmo.ru/
**Подробнее:** https://abit.itmo.ru/programs/master
        """

    def _save_conversation(self, user_id: str, username: str, message: str, response: str):
        """Save conversation to database"""
        try:
            conversation = Conversation()
            conversation.telegram_user_id = user_id
            conversation.username = username  
            conversation.message = message
            conversation.response = response
            db.session.add(conversation)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

def setup_bot():
    """Setup and configure the Telegram bot"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    bot = ITMOBot()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("profile", bot.profile))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    return application

def run_bot(application):
    """Run the Telegram bot"""
    try:
        logger.info("Starting bot polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
