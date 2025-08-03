import trafilatura
import re
from models import Program
from app import db
import logging

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    Extract main text content from a website using trafilatura
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            return text if text else ""
        return ""
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return ""

def parse_program_data(content: str, url: str) -> dict:
    """
    Parse program information from scraped content
    """
    data = {
        'description': '',
        'duration': '',
        'language': '',
        'cost': '',
        'budget_places': 0,
        'contract_places': 0,
        'career_prospects': '',
        'admission_requirements': '',
        'partners': [],
        'team_members': []
    }
    
    # Extract basic program info
    if 'длительность' in content.lower():
        duration_match = re.search(r'длительность[:\s]*(\d+\s*год[а-я]*)', content, re.IGNORECASE)
        if duration_match:
            data['duration'] = duration_match.group(1)
    
    if 'язык обучения' in content.lower():
        lang_match = re.search(r'язык обучения[:\s]*([а-я]+)', content, re.IGNORECASE)
        if lang_match:
            data['language'] = lang_match.group(1)
    
    # Extract cost information
    cost_match = re.search(r'(\d+\s*\d+\s*₽)', content)
    if cost_match:
        data['cost'] = cost_match.group(1)
    
    # Extract budget and contract places
    budget_match = re.search(r'(\d+)\s*бюджетных', content)
    if budget_match:
        data['budget_places'] = int(budget_match.group(1))
    
    contract_match = re.search(r'(\d+)\s*контрактных', content)
    if contract_match:
        data['contract_places'] = int(contract_match.group(1))
    
    # Extract program description (text after "о программе")
    desc_match = re.search(r'о программе.*?(?=партнеры программы|команда|учебный план)', content, re.IGNORECASE | re.DOTALL)
    if desc_match:
        data['description'] = desc_match.group(0).replace('о программе', '').strip()
    
    # Extract career information
    career_match = re.search(r'карьера.*?(?=ты сможешь работать|партнеры|отзывы)', content, re.IGNORECASE | re.DOTALL)
    if career_match:
        data['career_prospects'] = career_match.group(0).replace('карьера', '').strip()
    
    # Extract admission requirements
    admission_match = re.search(r'как поступить.*?(?=$)', content, re.IGNORECASE | re.DOTALL)
    if admission_match:
        data['admission_requirements'] = admission_match.group(0).replace('как поступить', '').strip()
    
    return data

def scrape_and_store_program_data():
    """
    Scrape data from both ITMO AI program pages and store in database
    """
    programs = [
        {
            'name': 'Искусственный интеллект',
            'url': 'https://abit.itmo.ru/program/master/ai'
        },
        {
            'name': 'Управление ИИ-продуктами/AI Product',
            'url': 'https://abit.itmo.ru/program/master/ai_product'
        }
    ]
    
    for program_info in programs:
        try:
            logger.info(f"Scraping program: {program_info['name']}")
            
            # Check if program already exists
            existing_program = Program.query.filter_by(url=program_info['url']).first()
            
            content = get_website_text_content(program_info['url'])
            if not content:
                logger.warning(f"No content scraped for {program_info['url']}")
                continue
            
            parsed_data = parse_program_data(content, program_info['url'])
            
            if existing_program:
                # Update existing program
                existing_program.name = program_info['name']
                existing_program.description = parsed_data['description']
                existing_program.duration = parsed_data['duration']
                existing_program.language = parsed_data['language']
                existing_program.cost = parsed_data['cost']
                existing_program.budget_places = parsed_data['budget_places']
                existing_program.contract_places = parsed_data['contract_places']
                existing_program.career_prospects = parsed_data['career_prospects']
                existing_program.admission_requirements = parsed_data['admission_requirements']
                existing_program.curriculum_data = {'raw_content': content}
                existing_program.partners = parsed_data['partners']
                existing_program.team_members = parsed_data['team_members']
            else:
                # Create new program
                new_program = Program()
                new_program.name = program_info['name']
                new_program.url = program_info['url']
                new_program.description = parsed_data['description']
                new_program.duration = parsed_data['duration']
                new_program.language = parsed_data['language']
                new_program.cost = parsed_data['cost']
                new_program.budget_places = parsed_data['budget_places']
                new_program.contract_places = parsed_data['contract_places']
                new_program.career_prospects = parsed_data['career_prospects']
                new_program.admission_requirements = parsed_data['admission_requirements']
                new_program.curriculum_data = {'raw_content': content}
                new_program.partners = parsed_data['partners']
                new_program.team_members = parsed_data['team_members']
                db.session.add(new_program)
            
            db.session.commit()
            logger.info(f"Successfully stored program: {program_info['name']}")
            
        except Exception as e:
            logger.error(f"Error processing program {program_info['name']}: {e}")
            db.session.rollback()
