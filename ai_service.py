import os
import json
import logging
from openai import OpenAI
from models import Program, UserProfile, Conversation
from app import db

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-openai-key"))
        self.model = "gpt-4o"

    async def generate_response(self, user_message: str, user_id: str) -> str:
        """Generate AI response for user message"""
        try:
            # Get or create user profile
            user_profile = UserProfile.query.filter_by(telegram_user_id=str(user_id)).first()
            if not user_profile:
                user_profile = UserProfile()
                user_profile.telegram_user_id = str(user_id)
                user_profile.survey_step = 0
                db.session.add(user_profile)
                db.session.commit()
            
            # Handle survey process first
            if user_profile.survey_step < 4:  # Survey not complete
                return await self._handle_survey(user_message, user_profile)
            
            # Get program data from database
            programs = Program.query.all()
            program_data = self._format_program_data(programs)
            
            profile_context = self._format_user_profile(user_profile)
            
            # Get recent conversation history
            recent_conversations = Conversation.query.filter_by(
                telegram_user_id=str(user_id)
            ).order_by(Conversation.created_at.desc()).limit(5).all()
            
            conversation_history = self._format_conversation_history(recent_conversations)
            
            # Check if question is relevant to ITMO AI programs
            if not self._is_relevant_question(user_message):
                return """
🤔 Я специализируюсь на вопросах о магистерских программах ИТМО в области искусственного интеллекта:

• Искусственный интеллект  
• Управление ИИ-продуктами/AI Product

Пожалуйста, задайте вопрос об этих программах, их содержании, поступлении или карьерных перспективах.
                """
            
            system_prompt = f"""
Вы - помощник по выбору магистерских программ ИТМО в области искусственного интеллекта. 
Отвечайте только на вопросы, связанные с двумя программами:
1. "Искусственный интеллект" 
2. "Управление ИИ-продуктами/AI Product"

ДАННЫЕ О ПРОГРАММАХ:
{program_data}

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
{profile_context}

ИСТОРИЯ РАЗГОВОРА:
{conversation_history}

ПРАВИЛА:
- Отвечайте только на русском языке
- Используйте только информацию из предоставленных данных о программах
- Если информации нет в данных, честно скажите об этом
- Давайте персональные рекомендации на основе профиля пользователя
- Будьте дружелюбны и полезны
- Если вопрос не связан с этими программами, вежливо перенаправьте
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content or "Извините, произошла ошибка при генерации ответа."
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Извините, произошла ошибка. Попробуйте позже или задайте вопрос по-другому."

    async def _handle_survey(self, user_message: str, user_profile: UserProfile) -> str:
        """Handle sequential survey to collect user background"""
        try:
            step = user_profile.survey_step
            
            if step == 0:  # Welcome message
                user_profile.survey_step = 1
                db.session.commit()
                return """
👋 Привет! Я помощник по выбору магистерских программ ИТМО в области ИИ.

Чтобы дать вам персональные рекомендации, мне нужно узнать о вашем бэкграунде.

📚 **Вопрос 1 из 4:** Расскажите о своем образовании. Какую степень и по какой специальности вы получили?

Например: "Бакалавр информатики", "Инженер-программист", "Экономист" и т.д.
                """
            
            elif step == 1:  # Education background
                user_profile.education_background = user_message
                user_profile.survey_step = 2
                db.session.commit()
                return """
💼 **Вопрос 2 из 4:** Расскажите о своем опыте работы. Сколько лет вы работаете и в какой сфере?

Например: "3 года разработчиком Python", "1 год аналитиком данных", "только начинаю карьеру" и т.д.
                """
            
            elif step == 2:  # Work experience  
                user_profile.work_experience = user_message
                user_profile.survey_step = 3
                db.session.commit()
                return """
🎯 **Вопрос 3 из 4:** Какие у вас карьерные цели? Кем вы видите себя после окончания магистратуры?

Например: "ML-инженер", "продакт-менеджер ИИ-продуктов", "исследователь" и т.д.
                """
            
            elif step == 3:  # Career goals
                user_profile.career_goals = user_message
                user_profile.survey_step = 4
                db.session.commit()
                
                # Generate personalized recommendation
                recommendation = await self._generate_recommendation(user_profile)
                
                return f"""
✅ **Спасибо за ответы!** 

На основе вашего профиля:
📚 Образование: {user_profile.education_background}
💼 Опыт: {user_profile.work_experience}  
🎯 Цели: {user_profile.career_goals}

{recommendation}

Теперь вы можете задавать любые вопросы о программах ИТМО! Я отвечу с учетом вашего бэкграунда.
                """
                
            return "Произошла ошибка в опросе. Попробуйте еще раз."
            
        except Exception as e:
            logger.error(f"Error in survey: {e}")
            return "Произошла ошибка при обработке опроса. Попробуйте еще раз."

    async def _generate_recommendation(self, user_profile: UserProfile) -> str:
        """Generate personalized program recommendation based on user profile"""
        try:
            programs = Program.query.all()
            program_data = self._format_program_data(programs)
            
            system_prompt = f"""
Вы эксперт по образовательным программам ИТМО. На основе профиля пользователя дайте персональную рекомендацию.

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
- Образование: {user_profile.education_background}
- Опыт работы: {user_profile.work_experience}
- Карьерные цели: {user_profile.career_goals}

ДОСТУПНЫЕ ПРОГРАММЫ:
{program_data}

Дайте краткую (до 200 слов) персональную рекомендацию:
1. Какая программа больше подходит и почему
2. На что обратить внимание при поступлении
3. Какие навыки стоит развивать

Отвечайте только на русском языке, будьте конкретны и полезны.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": system_prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content or "Не удалось сгенерировать рекомендацию."
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "📊 На основе вашего профиля я рекомендую изучить подробнее обе программы и задать конкретные вопросы о содержании курсов."

    def _format_program_data(self, programs) -> str:
        """Format program data for AI context"""
        if not programs:
            return "Данные о программах не загружены."
        
        formatted_data = ""
        for program in programs:
            formatted_data += f"""
ПРОГРАММА: {program.name}
URL: {program.url}
Описание: {program.description or 'Не указано'}
Длительность: {program.duration or 'Не указана'}
Язык: {program.language or 'Не указан'}
Стоимость: {program.cost or 'Не указана'}
Бюджетных мест: {program.budget_places or 0}
Контрактных мест: {program.contract_places or 0}
Карьерные перспективы: {program.career_prospects or 'Не указаны'}
Требования к поступлению: {program.admission_requirements or 'Не указаны'}

---
            """
        return formatted_data

    def _format_user_profile(self, profile: UserProfile) -> str:
        """Format user profile for AI context"""
        return f"""
Образование: {profile.education_background or 'не указано'}
Опыт работы: {profile.work_experience or 'не указан'}
Карьерные цели: {profile.career_goals or 'не указаны'}
Бэкграунд: {profile.background or 'не определен'}
        """

    def _format_conversation_history(self, conversations) -> str:
        """Format recent conversation history"""
        if not conversations:
            return "Нет предыдущих сообщений"
        
        history = ""
        for conv in reversed(conversations):  # Show oldest first
            history += f"Пользователь: {conv.message}\nБот: {conv.response}\n\n"
        
        return history

    def _is_relevant_question(self, message: str) -> bool:
        """Check if the question is relevant to ITMO AI programs"""
        message_lower = message.lower()
        
        # Keywords related to ITMO AI programs
        relevant_keywords = [
            'итмо', 'itmo', 'магистр', 'программа', 'искусственный интеллект', 'ai product',
            'машинное обучение', 'ml', 'ai', 'поступление', 'экзамен', 'бюджет',
            'контракт', 'карьера', 'работа', 'курс', 'дисциплина', 'проект',
            'партнер', 'стоимость', 'длительность', 'требования', 'диплом'
        ]
        
        # Check if message contains relevant keywords
        return any(keyword in message_lower for keyword in relevant_keywords)

    def analyze_student_fit(self, user_profile: UserProfile) -> dict:
        """Analyze which program fits better for the student"""
        try:
            profile_text = f"""
Бэкграунд: {user_profile.background}
Опыт: {user_profile.experience_years} лет  
Интересы: {', '.join(user_profile.interests) if user_profile.interests else 'не указаны'}
            """
            
            system_prompt = """
Проанализируйте профиль студента и определите, какая программа ИТМО лучше подходит:
1. "Искусственный интеллект" - техническая программа
2. "Управление ИИ-продуктами" - продуктовая программа

Ответьте в JSON формате:
{
  "recommended_program": "название программы",
  "confidence": "от 0 до 1",
  "reasoning": "объяснение выбора",
  "elective_courses": ["список рекомендуемых курсов"]
}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": profile_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            if result:
                return json.loads(result)
            else:
                return {
                    "recommended_program": "Не удалось определить",
                    "confidence": 0,
                    "reasoning": "Пустой ответ от модели",
                    "elective_courses": []
                }
            
        except Exception as e:
            logger.error(f"Error analyzing student fit: {e}")
            return {
                "recommended_program": "Не удалось определить",
                "confidence": 0,
                "reasoning": "Ошибка анализа профиля",
                "elective_courses": []
            }
